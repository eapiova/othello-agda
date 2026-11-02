/* AI-assisted read-only ZIP view. Every byte is verified by the coordinator.
 * No proof decisions are made here; Agda and exact cache provenance remain required.
 */
#define FUSE_USE_VERSION 31
#define _FILE_OFFSET_BITS 64
#include <fuse3/fuse.h>
#include <zip.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

static zip_t *archive;
static zip_int64_t entries;
struct opened { zip_file_t *stream; zip_uint64_t index; off_t position; };

/* Omit only regenerable table-data interfaces, preserving all source bytes. */
static int omitted(const char *name) {
    const char *prefixes[]={"_build/2.9.0/agda/src/Tests/TextUpperPacked6/Group",
                            "_build/2.9.0/agda/src/Tests/TextLowerPacked6/Group"};
    for (size_t k=0;k<2;k++) {
        size_t n=strlen(prefixes[k]);
        if(strncmp(name,prefixes[k],n)) continue;
        const char *p=name+n;
        if(*p<'0' || *p>'9') continue;
        while(*p>='0' && *p<='9') p++;
        if(!strcmp(p,".agdai")) return 1;
    }
    return 0;
}

static zip_int64_t locate(const char *path) {
    if (path[0] != '/' || strstr(path, "/../") || strlen(path) > 4094) return -1;
    if (omitted(path+1)) return -1;
    zip_int64_t i = zip_name_locate(archive, path+1, 0);
    if (i >= 0) return i;
    char directory[4096];
    snprintf(directory, sizeof(directory), "%s/", path+1);
    return zip_name_locate(archive, directory, 0);
}

static uint64_t little64(const unsigned char *p) {
    uint64_t value = 0;
    for (int i=7;i>=0;i--) value = (value << 8) | p[i];
    return value;
}

static int attributes(const char *path, struct stat *st, struct fuse_file_info *fi) {
    (void)fi;
    memset(st, 0, sizeof(*st));
    st->st_uid=getuid(); st->st_gid=getgid(); st->st_blksize=4096;
    if (!strcmp(path,"/")) { st->st_mode=S_IFDIR|0755; st->st_nlink=2; return 0; }
    zip_int64_t i=locate(path); if(i<0) return -ENOENT;
    zip_stat_t data; zip_stat_init(&data);
    if(zip_stat_index(archive,(zip_uint64_t)i,0,&data)<0) return -EIO;
    zip_uint8_t system; zip_uint32_t attr;
    if(zip_file_get_external_attributes(archive,(zip_uint64_t)i,0,&system,&attr)<0 || system!=ZIP_OPSYS_UNIX) return -EIO;
    st->st_mode=(mode_t)(attr>>16); st->st_nlink=S_ISDIR(st->st_mode)?2:1;
    if(!S_ISDIR(st->st_mode) && !S_ISREG(st->st_mode)) return -EIO;
    st->st_size=(off_t)data.size;
    st->st_blocks=(blkcnt_t)((data.comp_size+511)/512);
    zip_uint16_t length=0;
    const unsigned char *extra=zip_file_extra_field_get_by_id(archive,(zip_uint64_t)i,0xa6da,0,&length,ZIP_FL_CENTRAL);
    if(!extra || length!=8) return -EIO;
    uint64_t ns=little64(extra);
    st->st_mtim.tv_sec=(time_t)(ns/1000000000ULL); st->st_mtim.tv_nsec=(long)(ns%1000000000ULL);
    st->st_atim=st->st_mtim; st->st_ctim=st->st_mtim;
    return 0;
}

static int listing(const char *path, void *buffer, fuse_fill_dir_t fill, off_t offset,
                   struct fuse_file_info *fi, enum fuse_readdir_flags flags) {
    (void)offset; (void)fi; (void)flags;
    struct stat st; int result=attributes(path,&st,NULL);
    if(result) return result;
    if(!S_ISDIR(st.st_mode)) return -ENOTDIR;
    fill(buffer,".",NULL,0,0); fill(buffer,"..",NULL,0,0);
    char prefix[4096];
    if(!strcmp(path,"/")) prefix[0]=0;
    else snprintf(prefix,sizeof(prefix),"%s/",path+1);
    size_t size=strlen(prefix);
    for(zip_int64_t i=0;i<entries;i++) {
        const char *name=zip_get_name(archive,(zip_uint64_t)i,0);
        if(!name || omitted(name) || strncmp(name,prefix,size)) continue;
        const char *tail=name+size;
        if(!*tail) continue;
        const char *slash=strchr(tail,'/');
        if(slash && slash[1]) continue;
        char child[4096]; size_t n=slash?(size_t)(slash-tail):strlen(tail);
        if(!n || n>=sizeof(child)) return -EIO;
        memcpy(child,tail,n);child[n]=0;
        if(fill(buffer,child,NULL,0,0)) break;
    }
    return 0;
}

static int opening(const char *path, struct fuse_file_info *fi) {
    if((fi->flags&O_ACCMODE)!=O_RDONLY) return -EROFS;
    struct stat st;int result=attributes(path,&st,NULL);if(result)return result;
    if(!S_ISREG(st.st_mode))return -EISDIR;
    zip_int64_t i=locate(path);if(i<0)return -ENOENT;
    struct opened *handle=calloc(1,sizeof(*handle));if(!handle)return -ENOMEM;
    handle->index=(zip_uint64_t)i;handle->stream=zip_fopen_index(archive,handle->index,0);
    if(!handle->stream){free(handle);return -EIO;}
    fi->fh=(uint64_t)(uintptr_t)handle;fi->keep_cache=1;return 0;
}

static int reading(const char *path, char *buffer, size_t size, off_t offset, struct fuse_file_info *fi) {
    (void)path;
    if(offset<0 || size>16*1024*1024)return -EINVAL;
    struct opened *handle=(struct opened *)(uintptr_t)fi->fh;
    if(offset<handle->position){
        if(zip_fclose(handle->stream)<0)return -EIO;
        handle->stream=zip_fopen_index(archive,handle->index,0);handle->position=0;
        if(!handle->stream)return -EIO;
    }
    char scratch[32768];
    while(handle->position<offset){
        zip_uint64_t need=(zip_uint64_t)(offset-handle->position);
        if(need>sizeof(scratch))need=sizeof(scratch);
        zip_int64_t got=zip_fread(handle->stream,scratch,need);
        if(got<0)return -EIO;
        if(got==0)return 0;
        handle->position+=(off_t)got;
    }
    zip_int64_t got=zip_fread(handle->stream,buffer,(zip_uint64_t)size);
    if(got<0)return -EIO;
    handle->position+=(off_t)got;
    return (int)got;
}

static int releasing(const char *path, struct fuse_file_info *fi) {
    (void)path;struct opened *handle=(struct opened *)(uintptr_t)fi->fh;
    int result=zip_fclose(handle->stream);free(handle);return result<0?-EIO:0;
}

static int locking(const char *path, struct fuse_file_info *fi, int operation) {
    (void)path;(void)fi;(void)operation;
    /* This view is immutable; the coordinator also forbids overlapping checks.
       Locks here are process-local courtesy only and never authorize a writer. */
    return 0;
}

int main(int argc,char **argv){
    if(argc!=3){fprintf(stderr,"usage: archive-fs archive.zip empty-mountpoint\n");return 2;}
    int error=0;archive=zip_open(argv[1],ZIP_RDONLY,&error);
    if(!archive){fprintf(stderr,"ZIP open failed: %d\n",error);return 3;}
    entries=zip_get_num_entries(archive,0);
    if(entries<0 || entries>50000){zip_close(archive);return 4;}
    static struct fuse_operations operations={.getattr=attributes,.readdir=listing,
        .open=opening,.read=reading,.release=releasing,.flock=locking};
    char *args[]={argv[0],argv[2],"-f","-s","-o","ro",NULL};
    int result=fuse_main(6,args,&operations,NULL);
    if(zip_close(archive)<0 && !result)result=5;
    return result;
}
