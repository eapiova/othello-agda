/* Adapted with AI assistance; see README.md and vendor/LICENSE. */
/* 6x6 オセロの厳密解（改良版）
 *
 * solve6.c からの変更点：
 *   1. 置換表を「深い局面優先＋新しい局面用」の 2 スロット構成にした。
 *      元の版は衝突すると無条件に上書きしていたため、数の多い浅い局面が
 *      価値の高い深い局面を追い出していた。
 *   2. 置換表に最善手を保存し、次に同じ局面へ来たとき最初に試す。
 *   3. ETC（enhanced transposition cutoff）。子を展開する前に、
 *      子の局面を置換表で引いてカットオフできないか確かめる。
 *
 *   cc -O3 -march=native -o solve6b solve6b.c
 *   ./solve6b [TTビット数] [w:勝敗のみ]
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>
#include <stddef.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>

typedef uint64_t u64;
typedef unsigned __int128 u128;

static u64 REGION;

static inline int popc(u64 b) { return __builtin_popcountll(b); }

#define MASK_A  0xfefefefefefefefeULL
#define MASK_H  0x7f7f7f7f7f7f7f7fULL

static inline u64 shift_dir(u64 b, int d) {
  switch (d) {
    case 0: return (b << 1) & MASK_A;
    case 1: return (b >> 1) & MASK_H;
    case 2: return  b << 8;
    case 3: return  b >> 8;
    case 4: return (b << 9) & MASK_A;
    case 5: return (b << 7) & MASK_H;
    case 6: return (b >> 7) & MASK_A;
    default:return (b >> 9) & MASK_H;
  }
}

static u64 gen_moves(u64 P, u64 O) {
  u64 empty = ~(P | O) & REGION;
  u64 moves = 0;
  for (int d = 0; d < 8; d++) {
    u64 t = shift_dir(P, d) & O;
    t |= shift_dir(t, d) & O;
    t |= shift_dir(t, d) & O;
    t |= shift_dir(t, d) & O;
    t |= shift_dir(t, d) & O;
    moves |= shift_dir(t, d) & empty;
  }
  return moves;
}

static u64 gen_flips(u64 P, u64 O, u64 m) {
  u64 flips = 0;
  for (int d = 0; d < 8; d++) {
    u64 t = shift_dir(m, d) & O, line = t;
    for (int k = 0; k < 4 && t; k++) { t = shift_dir(t, d) & O; line |= t; }
    if (shift_dir(line, d) & P) flips |= line;
  }
  return flips;
}

/* ---------- 置換表：深さ優先スロット＋新しさ優先スロット ---------- */
typedef struct { u64 P, O; int16_t lo, hi; uint8_t empties, move, valid; } TTE;
typedef struct { TTE deep, fresh; } Bucket;
static Bucket *tt; static u64 tt_mask;
static int oracle_aborted = 0;

static int selftest_constant_hash = 0;
static inline u64 hashkey(u64 P, u64 O) {
  if (selftest_constant_hash) return 0;
  u128 h = (u128)(P ^ 0x9e3779b97f4a7c15ULL) * 0xff51afd7ed558ccdULL;
  h ^= (u128)(O + 0xc4ceb9fe1a85ec53ULL) * 0x9e3779b97f4a7c15ULL;
  return (u64)h ^ (u64)(h >> 64);
}

/* P/O are relative to the side to move. No symmetry normalization is used.
 * Hashes select buckets only; every hit compares both complete board words.
 * Explicit validity also prevents zero-initialized slots matching real boards. */
static u64 tt_hits = 0, tt_collisions = 0;
static inline TTE *tt_probe(u64 P, u64 O, int empties) {
  Bucket *b = &tt[hashkey(P, O) & tt_mask];
  TTE *slots[2] = { &b->deep, &b->fresh };
  for (int i = 0; i < 2; i++) {
    TTE *e = slots[i];
    if (!e->valid) continue;
    if (e->P == P && e->O == O && e->empties == (uint8_t)empties) {
      tt_hits++; return e;
    }
    tt_collisions++;
  }
  return NULL;
}
static inline void tt_store(u64 P, u64 O, int empties, int lo, int hi, int mv) {
  /* A capped descendant returns a placeholder, not a score bound. Never let
   * that placeholder enter the table reused by a later frontier case. */
  if (oracle_aborted) return;
  Bucket *b = &tt[hashkey(P, O) & tt_mask];
  TTE *slot;
  if (b->deep.valid && b->deep.P == P && b->deep.O == O) slot = &b->deep;
  else if (!b->deep.valid || empties >= b->deep.empties) slot = &b->deep;
  else slot = &b->fresh;
  slot->P = P; slot->O = O; slot->valid = 1;
  slot->empties = (uint8_t)empties;
  slot->lo = (int16_t)lo; slot->hi = (int16_t)hi; slot->move = (uint8_t)mv;
}
static u64 nodes = 0;

/* Bounded, untrusted bound-proof prefix. Full keys; no symmetry quotient. */
static u64 oracle_cap = 0;
static u64 native_calls = 0;
static clock_t oracle_start;
static int oracle_cpu_cap = 0;
static int oracle_stop(void) {
  if (oracle_aborted) return 1;
  if ((oracle_cap && nodes >= oracle_cap) ||
      (oracle_cpu_cap && (nodes & 1023) == 0 &&
       (double)(clock()-oracle_start)/CLOCKS_PER_SEC >= oracle_cpu_cap)) {
    oracle_aborted = 1; return 1;
  }
  return 0;
}

static int SMALL = 10;   /* この空きマス数以下は表を使わず読み切る */
static int DEEPORD = 13; /* この空きマス数以上で着手数による並べ替えをする */
static int ORDER[64], ORDER_N;

static int solve(u64 P, u64 O, int alpha, int beta);

/* 残り 10 マス以下は表を使わず読み切る */
static int solve_small(u64 P, u64 O, int alpha, int beta) {
  if (oracle_stop()) return 0;
  nodes++;
  u64 moves = gen_moves(P, O);
  if (!moves) {
    if (!gen_moves(O, P)) return popc(P) - popc(O);
    return -solve_small(O, P, -beta, -alpha);
  }
  int best = -64;
  for (int i = 0; i < ORDER_N; i++) {
    u64 m = 1ULL << ORDER[i];
    if (!(moves & m)) continue;
    u64 f = gen_flips(P, O, m);
    int v = -solve_small(O ^ f, P ^ f ^ m, -beta, -alpha);
    if (v > best) best = v;
    if (best > alpha) alpha = best;
    if (alpha >= beta) break;
  }
  return best;
}

static int solve(u64 P, u64 O, int alpha, int beta) {
  if (oracle_stop()) return 0;
  int empties = popc(~(P | O) & REGION);
  if (empties <= SMALL) return solve_small(P, O, alpha, beta);

  nodes++;
  int a0 = alpha, b0 = beta, ttmove = 64;
  TTE *e = tt_probe(P, O, empties);
  if (e) {
    if (e->lo >= beta) return e->lo;
    if (e->hi <= alpha) return e->hi;
    if (e->lo > alpha) alpha = e->lo;
    if (e->hi < beta)  beta  = e->hi;
    if (alpha >= beta) return alpha;
    ttmove = e->move;
  }

  u64 moves = gen_moves(P, O);
  if (!moves) {
    if (!gen_moves(O, P)) return popc(P) - popc(O);
    return -solve(O, P, -beta, -alpha);
  }

  /* 手を並べる：置換表の手 → 相手の着手可能数が少ない手 */
  int idx[36] = {0}, sc[36], n = 0;
  u64 flip[36], np_[36], no_[36];
  int deep = (empties >= DEEPORD);
  for (int i = 0; i < ORDER_N; i++) {
    int sq = ORDER[i];
    u64 m = 1ULL << sq;
    if (!(moves & m)) continue;
    u64 f = gen_flips(P, O, m);
    flip[n] = f; np_[n] = P ^ f ^ m; no_[n] = O ^ f;
    idx[n] = sq;
    sc[n] = (sq == ttmove) ? 10000 : (deep ? -popc(gen_moves(no_[n], np_[n])) * 4 : 0);
    n++;
  }
  if (deep || ttmove != 64) for (int i = 1; i < n; i++) {
    int ki = idx[i], ks = sc[i]; u64 kf = flip[i], kp = np_[i], ko = no_[i];
    int j = i - 1;
    while (j >= 0 && sc[j] < ks) {
      idx[j+1] = idx[j]; sc[j+1] = sc[j];
      flip[j+1] = flip[j]; np_[j+1] = np_[j]; no_[j+1] = no_[j];
      j--;
    }
    idx[j+1] = ki; sc[j+1] = ks; flip[j+1] = kf; np_[j+1] = kp; no_[j+1] = ko;
  }

  /* ETC: 子を実際に探索する前に、表だけでカットオフできないか見る */
  if (empties >= 14) {
    int ce = empties - 1;
    for (int i = 0; i < n; i++) {
      TTE *c = tt_probe(no_[i], np_[i], ce);
      if (c && -c->hi >= beta) { tt_store(P, O, empties, -c->hi, 64, idx[i]); return -c->hi; }
    }
  }

  int best = -64, bestmv = idx[0];
  for (int i = 0; i < n; i++) {
    int v;
    if (i == 0) v = -solve(no_[i], np_[i], -beta, -alpha);
    else {
      v = -solve(no_[i], np_[i], -alpha - 1, -alpha);
      if (v > alpha && v < beta) v = -solve(no_[i], np_[i], -beta, -v);
    }
    if (v > best) { best = v; bestmv = idx[i]; }
    if (best > alpha) alpha = best;
    if (alpha >= beta) break;
  }

  if (oracle_aborted) return 0;
  if (best <= a0)      tt_store(P, O, empties, -64,  best, bestmv);
  else if (best >= b0) tt_store(P, O, empties, best, 64,   bestmv);
  else                 tt_store(P, O, empties, best, best, bestmv);
  return best;
}


/* CLI coordinates are zero-based row-major; internal bits use a padded 8x8
 * layout with the 6x6 board in rows/columns 1..6. */
static int sq(int index) { return (index / 6 + 1) * 8 + index % 6 + 1; }
static void encode(u64 P, u64 O, int white_turn, char out[37]) {
  for (int i = 0; i < 36; i++) {
    u64 m = 1ULL << sq(i);
    out[i] = P & m ? (white_turn ? '2' : '1') : O & m ? (white_turn ? '1' : '2') : '0';
  }
  out[36] = '\0';
}
static u64 perft(u64 P, u64 O, int depth) {
  nodes++;
  if (!depth) return 1;
  u64 moves = gen_moves(P, O), total = 0;
  if (!moves) return gen_moves(O, P) ? perft(O, P, depth - 1) : 0;
  while (moves) {
    u64 m = moves & -moves; moves ^= m;
    u64 f = gen_flips(P, O, m);
    total += perft(O ^ f, P ^ f ^ m, depth - 1);
  }
  return total;
}
/* Literal lazy Game.Search.forces mirror: no table or search hints. */
static int mirror(u64 P, u64 O, int white_turn, int lower, int threshold, int fuel) {
  nodes++;
  if (!fuel) return 0;
  u64 moves = gen_moves(P, O);
  if (!moves) {
    if (gen_moves(O, P)) return mirror(O, P, !white_turn, lower, threshold, fuel - 1);
    int raw = white_turn ? popc(P) - popc(O) : popc(O) - popc(P);
    return lower ? raw >= threshold : raw <= threshold;
  }
  int own = white_turn == lower;
  /* Padded low bits traverse precisely the public row-major sequence. */
  while (moves) {
    u64 m = moves & -moves; moves ^= m;
    u64 f = gen_flips(P, O, m);
    int holds = mirror(O ^ f, P ^ f ^ m, !white_turn, lower, threshold, fuel - 1);
    if (holds == own) return own;
  }
  return !own;
}
typedef struct {
  u64 P, O, tree, hints;
  int threshold;
  unsigned char turn, lower, status, leaf;
  int selected;
} PrefixState;
static PrefixState *prefix;
static uint32_t *prefix_slots;
static size_t prefix_count, prefix_limit, prefix_slot_count;
static u64 prefix_leaves, prefix_edges, prefix_repeats;
static int prefix_incomplete, prefix_overflow, frontier_discs;
static u64 add_count(u64 a, u64 b) {
  if (UINT64_MAX-a < b) { prefix_overflow=1; return UINT64_MAX; }
  return a+b;
}
static int bound_holds(u64 P, u64 O, int turn, int lower, int threshold) {
  native_calls++;
  int alpha = turn ? (lower ? threshold-1 : threshold) : (lower ? -threshold : -threshold-1);
  int result=solve(P,O,alpha,alpha+1);
  if (oracle_aborted) return 0;
  int raw=turn ? result : -result;
  return lower ? raw>=threshold : raw<=threshold;
}
static size_t visit_prefix(u64 P,u64 O,int turn,int lower,int threshold) {
  if (prefix_incomplete || oracle_stop()) { prefix_incomplete=1; return SIZE_MAX; }
  u64 h=hashkey(P,O) ^ ((u64)(threshold+36)<<2) ^ (u64)(turn*2+lower);
  size_t slot=(size_t)h & (prefix_slot_count-1);
  while (prefix_slots[slot]) {
    size_t id=prefix_slots[slot]-1; PrefixState *s=&prefix[id];
    if(s->P==P && s->O==O && s->turn==turn && s->lower==lower && s->threshold==threshold) {
      prefix_repeats++;
      /* Every move increases discs; a pass is followed by a legal move.
       * A visiting-state hit would violate this acyclic measure. */
      if(s->status==1) prefix_incomplete=1;
      return id;
    }
    slot=(slot+1)&(prefix_slot_count-1);
  }
  if(prefix_count==prefix_limit) { prefix_incomplete=1; return SIZE_MAX; }
  size_t id=prefix_count++; prefix_slots[slot]=(uint32_t)(id+1);
  PrefixState *s=&prefix[id];
  *s=(PrefixState){.P=P,.O=O,.threshold=threshold,.turn=turn,.lower=lower,.status=1,.tree=1,.selected=-1};
  u64 moves=gen_moves(P,O);
  int terminal=!moves && !gen_moves(O,P);
  if(terminal || popc(P|O)>=frontier_discs) {
    s->leaf=1; prefix_leaves++;
    if(terminal) { int raw=turn ? popc(P)-popc(O) : popc(O)-popc(P);
      if (!(lower ? raw>=threshold : raw<=threshold)) prefix_incomplete=1; }
    s->status=2; return id;
  }
  if(!moves) {
    prefix_edges++;
    size_t child=visit_prefix(O,P,!turn,lower,threshold);
    if(child!=SIZE_MAX) { s->tree=add_count(s->tree,prefix[child].tree); s->hints=prefix[child].hints; }
  } else {
    int own=turn==lower, index=0, selected=0;
    while(moves && !prefix_incomplete) {
      u64 m=moves & -moves; moves^=m; u64 f=gen_flips(P,O,m);
      u64 cp=O^f, co=P^f^m;
      if(!own || bound_holds(cp,co,!turn,lower,threshold)) {
        if(own) { s->selected=index; s->hints=1; selected=1; }
        prefix_edges++;
        size_t child=visit_prefix(cp,co,!turn,lower,threshold);
        if(child!=SIZE_MAX) { s->tree=add_count(s->tree,prefix[child].tree); s->hints=add_count(s->hints,prefix[child].hints); }
        if(own) break;
      }
      if(oracle_aborted) { prefix_incomplete=1; break; }
      index++;
    }
    if(own && !selected) prefix_incomplete=1;
  }
  s->status=2; return id;
}

static int integer(const char *s, int lo, int hi, int *out) {
  char *end; long v = strtol(s, &end, 10);
  if (!*s || *end || v < lo || v > hi) return 0;
  *out = (int)v; return 1;
}
static int node_limit(const char *s, u64 *out) {
  if (!*s) return 0;
  for (const char *p=s; *p; p++) if (*p<'0' || *p>'9') return 0;
  char *end; errno=0; unsigned long long value=strtoull(s,&end,10);
  if(errno==ERANGE || *end || value<1 || value>1000000000000ULL) return 0;
  *out=(u64)value; return 1;
}
static int error(const char *message) {
  fprintf(stderr, "{\"error\":\"%s\"}\n", message); return 2;
}
static int run_frontier(u64 P,u64 O,int white_turn,const char *direction,int threshold,
    int max_states,u64 max_nodes,int max_memory_mb,int max_cpu_seconds,int emit_states,int ttbits,clock_t whole_start) {
    clock_t start=clock(); size_t ttn=(size_t)1<<ttbits;
    u64 before_nodes=nodes,before_calls=native_calls,before_hits=tt_hits,before_collisions=tt_collisions;
    prefix_count=0; prefix_leaves=prefix_edges=prefix_repeats=0;
    prefix_incomplete=prefix_overflow=0;
    prefix_limit=(size_t)max_states; prefix_slot_count=1;
    while(prefix_slot_count<prefix_limit*2) prefix_slot_count*=2;
    size_t bytes=ttn*sizeof(Bucket)+prefix_limit*sizeof(PrefixState)+prefix_slot_count*sizeof(uint32_t);
    if(bytes>(size_t)max_memory_mb*1024*1024) { return error("requested tables exceed memory cap"); }
    prefix=calloc(prefix_limit,sizeof(PrefixState)); prefix_slots=calloc(prefix_slot_count,sizeof(uint32_t));
    if(!prefix || !prefix_slots) { free(prefix); free(prefix_slots); return error("cannot allocate frontier tables"); }
    oracle_cap=nodes+max_nodes; oracle_cpu_cap=max_cpu_seconds; oracle_start=start;
    oracle_aborted=0;
    int lower=!strcmp(direction,"lower");
    int root_holds=bound_holds(P,O,white_turn,lower,threshold);
    int root_validated=!oracle_aborted;
    if(root_holds) visit_prefix(P,O,white_turn,lower,threshold);
    if(oracle_aborted) prefix_incomplete=1;
    u64 tree=prefix_count ? prefix[0].tree : 0, hints=prefix_count ? prefix[0].hints : 0;
    int complete=root_validated && root_holds && !prefix_incomplete && !prefix_overflow;
    printf("{\"direction\":\"%s\",\"threshold\":%d,\"root_validated\":%s,\"root_holds\":%s,\"complete\":%s,\"frontier_discs\":%d,\"tree_nodes_S\":%llu,\"tree_count_kind\":\"%s\",\"unique_dag_nodes\":%zu,\"frontier_distinct_L\":%llu,\"hint_occurrences_H\":%llu,\"dag_edges\":%llu,\"dedup_hits\":%llu,\"tree_dag_ratio\":%.6f,\"count_overflow\":%s,\"allocated_bytes\":%zu,\"oracle_aborted\":%s,\"line_maintained\":false,\"trust\":\"untrusted native instrumentation\"",
      direction,threshold,root_validated?"true":"false",root_holds?"true":"false",complete?"true":"false",frontier_discs,
      (unsigned long long)tree,complete?"exact":"lower-bound",prefix_count,(unsigned long long)prefix_leaves,
      (unsigned long long)hints,(unsigned long long)prefix_edges,(unsigned long long)prefix_repeats,
      prefix_count?(double)tree/prefix_count:0,prefix_overflow?"true":"false",bytes,oracle_aborted?"true":"false");
    if(emit_states) {
      printf(",\"states\":[");
      for(size_t i=0;i<prefix_count;i++) { char pos[37]; PrefixState *s=&prefix[i]; encode(s->P,s->O,s->turn,pos);
        printf("%s{\"position\":\"%s\",\"turn\":\"%s\",\"direction\":\"%s\",\"threshold\":%d,\"leaf\":%s,\"selected_index\":%d}",i?",":"",pos,s->turn?"white":"black",s->lower?"lower":"upper",s->threshold,s->leaf?"true":"false",s->selected);
      }
      printf("]");
    }
    printf(",\"record_type\":\"frontier\",\"nodes\":%llu,\"native_calls\":%llu,\"tt_hits\":%llu,\"tt_collisions\":%llu,\"tt_bits\":%d,\"tt_bytes\":%zu,\"cpu_seconds\":%.6f,\"cumulative_nodes\":%llu,\"cumulative_cpu_seconds\":%.6f}\n",
      (unsigned long long)(nodes-before_nodes),(unsigned long long)(native_calls-before_calls),
      (unsigned long long)(tt_hits-before_hits),(unsigned long long)(tt_collisions-before_collisions),
      ttbits,ttn*sizeof(Bucket),(double)(clock()-start)/CLOCKS_PER_SEC,
      (unsigned long long)nodes,(double)(clock()-whole_start)/CLOCKS_PER_SEC);
    fflush(stdout);
    free(prefix); free(prefix_slots); prefix=NULL; prefix_slots=NULL;
    return complete ? 0 : 1;
}
/* Host-ABI snapshots are untrusted search hints, never proof input. Streaming
 * reads/writes need no second table allocation. Python binds a SHA256 sidecar. */
static int checkpoint(const char *path, int saving, int bits) {
  uint64_t header[16] = {0x3654544f4c4c4548ULL, 1, (uint64_t)bits,
    sizeof(Bucket), sizeof(TTE), sizeof(size_t), sizeof(int),
    0x0102030405060708ULL, offsetof(TTE, lo), offsetof(TTE, empties),
    offsetof(TTE, valid), offsetof(Bucket, fresh), (uint64_t)SMALL,
    (uint64_t)DEEPORD, ((uint64_t)1 << bits)*sizeof(Bucket), sizeof(header)};
  size_t bytes=(size_t)header[14];
  if (!saving) {
    FILE *f=fopen(path,"rb"); struct stat st; uint64_t actual[16];
    if (!f) return error("cannot open TT checkpoint");
    int ok=fstat(fileno(f),&st)==0 && S_ISREG(st.st_mode) &&
      (uint64_t)st.st_size==sizeof(header)+(uint64_t)bytes &&
      fread(actual,1,sizeof(actual),f)==sizeof(actual) &&
      !memcmp(header,actual,sizeof(header)) && fread(tt,1,bytes,f)==bytes && !ferror(f);
    fclose(f);
    return ok ? 0 : error("TT checkpoint header, ABI, configuration or size mismatch");
  }
  size_t n=strlen(path)+16; char *tmp=malloc(n);
  if (!tmp) return error("cannot allocate checkpoint filename");
  snprintf(tmp,n,"%s.tmp-XXXXXX",path); int fd=mkstemp(tmp);
  if(fd<0) { free(tmp); return error("cannot create temporary TT checkpoint"); }
  FILE *f=fdopen(fd,"wb"); int ok=f!=NULL;
  if(f) {
    ok=fwrite(header,1,sizeof(header),f)==sizeof(header) && fwrite(tt,1,bytes,f)==bytes;
    if(fflush(f) || fsync(fd)) ok=0;
    if(fclose(f)) ok=0;
  } else close(fd);
  /* Reserve a previously absent destination before atomic rename. Never replace
   * an unrelated preexisting file, including a symlink. */
  int target=-1;
  if(ok) { target=open(path,O_WRONLY|O_CREAT|O_EXCL,0600); if(target<0) ok=0; }
  if(target>=0) { close(target); if(rename(tmp,path)) { unlink(path); ok=0; } }
  unlink(tmp); free(tmp);
  return ok ? 0 : error("cannot save TT checkpoint (destination must be absent)");
}
int main(int argc, char **argv) {
  const char *save_tt=NULL, *load_tt=NULL;
  const char *grid="18,20,22,24,26,28"; int baseline_cpu_seconds=7200, threshold_set=0;
  const char *cmd = argc > 1 ? argv[1] : "", *position = "initial", *direction = "lower";
  u64 max_nodes=10000000;
  int max_states=1000000, max_memory_mb=512, max_cpu_seconds=20, emit_states=0;
  frontier_discs=26;
  int white_turn = 0, ttbits = 18, depth = -1, threshold = 0, fuel = 80;
  if (strcmp(cmd,"solve") && strcmp(cmd,"bounds") && strcmp(cmd,"moves") &&
      strcmp(cmd,"study") && strcmp(cmd,"frontier") && strcmp(cmd,"perft") && strcmp(cmd,"mirror") && strcmp(cmd,"tt-selftest")) return error("unknown command");
  for (int i = 2; i < argc; i += 2) {
    if (i + 1 == argc) return error("option requires value");
    const char *flag = argv[i], *v = argv[i+1];
    if (!strcmp(flag,"--save-tt")) save_tt=v;
    else if (!strcmp(flag,"--load-tt")) load_tt=v;
    else if (!strcmp(flag,"--frontier-grid")) grid=v;
    else if (!strcmp(flag,"--baseline-cpu-seconds")) { if(!integer(v,1,86400,&baseline_cpu_seconds)) return error("invalid baseline CPU cap"); }
    else if (!strcmp(flag,"--frontier-discs")) { if(!integer(v,0,36,&frontier_discs)) return error("invalid frontier discs"); }
    else if (!strcmp(flag,"--max-states")) { if(!integer(v,1,100000000,&max_states)) return error("invalid max states"); }
    else if (!strcmp(flag,"--max-nodes")) { if(!node_limit(v,&max_nodes)) return error("invalid max nodes"); }
    else if (!strcmp(flag,"--max-memory-mb")) { if(!integer(v,1,8192,&max_memory_mb)) return error("invalid memory cap"); }
    else if (!strcmp(flag,"--max-cpu-seconds")) { if(!integer(v,1,86400,&max_cpu_seconds)) return error("invalid CPU cap"); }
    else if (!strcmp(flag,"--emit-states")) { if(!integer(v,0,1,&emit_states)) return error("emit states must be 0 or 1"); }
    else if (!strcmp(flag,"--position")) position = v;
    else if (!strcmp(flag,"--turn")) {
      if (strcmp(v,"white") && strcmp(v,"black")) return error("invalid turn");
      white_turn = !strcmp(v,"white");
    } else if (!strcmp(flag,"--tt-bits")) {
      if (!integer(v,0,26,&ttbits)) return error("tt bits must be 0..26");
    } else if (!strcmp(flag,"--small")) {
      if (!integer(v,0,36,&SMALL)) return error("small must be 0..36");
    } else if (!strcmp(flag,"--deep-order")) {
      if (!integer(v,0,36,&DEEPORD)) return error("deep order must be 0..36");
    } else if (!strcmp(flag,"--fuel")) {
      if (!integer(v,0,1000000,&fuel)) return error("fuel must be 0..1000000");
    } else if (!strcmp(flag,"--depth")) {
      /* Intended for short cross-checks; avoids overflowing a uint64 path count. */
      if (!integer(v,0,10,&depth)) return error("depth must be 0..10");
    } else if (!strcmp(flag,"--threshold")) {
      threshold_set=1;
      if (!integer(v,-36,36,&threshold)) return error("threshold must be -36..36");
    } else if (!strcmp(flag,"--direction")) {
      if (strcmp(v,"lower") && strcmp(v,"upper")) return error("invalid direction");
      direction = v;
    } else return error("unknown option");
  }
  int grid_values[37], grid_count=0;
  if(!strcmp(cmd,"study")) {
    if(!threshold_set) threshold=4;
    const char *g=grid;
    while(*g) { char *end; long n=strtol(g,&end,10);
      if(end==g || n<0 || n>36 || grid_count==37 || (*end && *end!=',')) return error("invalid frontier grid");
      grid_values[grid_count++]=(int)n;
      if(!*end) break;
      g=end+1; if(!*g) return error("invalid frontier grid");
    }
    if(!grid_count) return error("empty frontier grid");
  }
  REGION = 0; ORDER_N = 0;
  for (int i = 0; i < 36; i++) { REGION |= 1ULL << sq(i); ORDER[ORDER_N++] = sq(i); }
  int weights[36];
  for (int i = 0; i < 36; i++) {
    int r = i / 6, c = i % 6, dr = r < 3 ? r : 5-r, dc = c < 3 ? c : 5-c;
    weights[i] = -3 * (dr + dc);
    if ((dr == 0 && dc == 1) || (dr == 1 && dc == 0) || (dr == 1 && dc == 1)) weights[i] -= 20;
    if (dr == 0 && dc == 0) weights[i] += 40;
  }
  for (int i = 1; i < ORDER_N; i++) {
    int move = ORDER[i], weight = weights[i], j = i - 1;
    while (j >= 0 && weights[j] < weight) { ORDER[j+1] = ORDER[j]; weights[j+1] = weights[j]; j--; }
    ORDER[j+1] = move; weights[j+1] = weight;
  }
  u64 B = 0, W = 0;
  if (!strcmp(position,"initial")) {
    B = (1ULL << sq(15)) | (1ULL << sq(20));
    W = (1ULL << sq(14)) | (1ULL << sq(21));
  } else {
    if (strlen(position) != 36) return error("position must have 36 cells");
    for (int i = 0; i < 36; i++) {
      if (position[i] == '1') B |= 1ULL << sq(i);
      else if (position[i] == '2') W |= 1ULL << sq(i);
      else if (position[i] != '0') return error("position cells must be 0,1,2");
    }
  }
  u64 P = white_turn ? W : B, O = white_turn ? B : W;
  if (!strcmp(cmd,"perft") && depth < 0) return error("perft requires depth");
  if ((save_tt || load_tt) && strcmp(cmd,"solve") && strcmp(cmd,"bounds") &&
      strcmp(cmd,"study") && strcmp(cmd,"frontier")) return error("TT checkpoints unsupported for command");
  size_t ttn = (size_t)1 << ttbits;
  if (!strcmp(cmd,"frontier") || !strcmp(cmd,"study")) {
    size_t slots=1;
    while(slots<(size_t)max_states*2) slots*=2;
    size_t requested=ttn*sizeof(Bucket)+(size_t)max_states*sizeof(PrefixState)+slots*sizeof(uint32_t);
    if(requested>(size_t)max_memory_mb*1024*1024) return error("requested tables exceed memory cap");
  }
  if (!strcmp(cmd,"solve") || !strcmp(cmd,"bounds") || !strcmp(cmd,"study") || !strcmp(cmd,"frontier") || !strcmp(cmd,"tt-selftest")) {
    tt = calloc(ttn,sizeof(Bucket));
    if (!tt) return error("cannot allocate transposition table");
    tt_mask = ttn - 1;
  }
  if(load_tt && checkpoint(load_tt,0,ttbits)) { free(tt); return 2; }
  clock_t start = clock();
  if (!strcmp(cmd,"study")) {
    oracle_start=start; oracle_cpu_cap=baseline_cpu_seconds; oracle_cap=0;
    native_calls++;
    int relative=solve(P,O,-64,64), value=white_turn?relative:-relative;
    int exact_complete=!oracle_aborted;
    if(save_tt && exact_complete && checkpoint(save_tt,1,ttbits)) { free(tt); return 2; }
    printf("{\"record_type\":\"exact\",\"complete\":%s,\"value\":",exact_complete?"true":"false");
    if(exact_complete) printf("%d",value); else printf("null");
    printf(",\"threshold\":%d,\"threshold_matches_value\":%s,\"nodes\":%llu,\"native_calls\":1,\"cpu_seconds\":%.6f,\"tt_bits\":%d,\"tt_bytes\":%zu,\"tt_hits\":%llu,\"tt_collisions\":%llu,\"oracle_aborted\":%s,\"scoring\":\"white-minus-black\",\"trust\":\"untrusted native instrumentation\",\"bounds_derived_from_exact\":true,\"bounds\":",
      threshold,exact_complete&&value==threshold?"true":"false",(unsigned long long)nodes,
      (double)(clock()-start)/CLOCKS_PER_SEC,ttbits,ttn*sizeof(Bucket),(unsigned long long)tt_hits,
      (unsigned long long)tt_collisions,oracle_aborted?"true":"false");
    if(exact_complete) printf("{\"ge4\":%s,\"ge5\":%s,\"le4\":%s,\"le3\":%s}",value>=4?"true":"false",value>=5?"true":"false",value<=4?"true":"false",value<=3?"true":"false"); else printf("null");
    printf("}\n"); fflush(stdout);
    int cases=0, complete_cases=0;
    if(exact_complete && value==threshold) {
      for(int i=0;i<grid_count;i++) for(int lower=1;lower>=0;lower--) {
        frontier_discs=grid_values[i]; cases++;
        int rc=run_frontier(P,O,white_turn,lower?"lower":"upper",threshold,max_states,max_nodes,max_memory_mb,max_cpu_seconds,emit_states,ttbits,start);
        if(rc==0) complete_cases++;
      }
    }
    printf("{\"record_type\":\"summary\",\"exact_complete\":%s,\"cases\":%d,\"complete_cases\":%d,\"skipped_grid\":%s,\"complete\":%s,\"nodes\":%llu,\"native_calls\":%llu,\"cpu_seconds\":%.6f,\"tt_reused\":true,\"line_maintained\":false,\"trust\":\"untrusted native instrumentation\"}\n",
      exact_complete?"true":"false",cases,complete_cases,cases?"false":"true",
      exact_complete&&cases>0&&cases==complete_cases?"true":"false",(unsigned long long)nodes,
      (unsigned long long)native_calls,(double)(clock()-start)/CLOCKS_PER_SEC);
    fflush(stdout); free(tt); return 0;
  }
  if (!strcmp(cmd,"frontier")) {
    run_frontier(P,O,white_turn,direction,threshold,max_states,max_nodes,max_memory_mb,max_cpu_seconds,emit_states,ttbits,start);
    if(save_tt && checkpoint(save_tt,1,ttbits)) { free(tt); return 2; }
    free(tt); return 0;
  } else
  if (!strcmp(cmd,"tt-selftest")) {
    /* Even identical 64-bit hashes must never identify different positions. */
    selftest_constant_hash = 1;
    int empty_miss = tt_probe(1,2,34) == NULL;
    tt_store(1,2,34,7,7,64);
    int hit = tt_probe(1,2,34) != NULL;
    int collision_miss = tt_probe(4,8,34) == NULL;
    int turn_miss = tt_probe(2,1,34) == NULL;
    printf("{\"ok\":%s,\"forced_equal_hash\":true", empty_miss && hit && collision_miss && turn_miss ? "true" : "false");
  } else if (!strcmp(cmd,"moves")) {
    u64 moves = gen_moves(P,O); int comma = 0;
    printf("{\"successors\":[");
    for (int i = 0; i < 36; i++) if (moves & (1ULL << sq(i))) {
      u64 m = 1ULL << sq(i), f = gen_flips(P,O,m); char pos[37];
      encode(O ^ f, P ^ f ^ m, !white_turn, pos);
      printf("%s{\"index\":%d,\"move\":[%d,%d],\"position\":\"%s\",\"turn\":\"%s\"}",
             comma ? "," : "", comma, i / 6, i % 6, pos, white_turn ? "black" : "white");
      comma++;
    }
    if (!moves && gen_moves(O,P)) {
      char pos[37]; encode(P,O,white_turn,pos);
      printf("{\"index\":0,\"move\":\"pass\",\"position\":\"%s\",\"turn\":\"%s\"}", pos, white_turn ? "black" : "white");
      comma = 1;
    }
    printf("],\"terminal\":%s", comma ? "false" : "true");
  } else if (!strcmp(cmd,"perft")) {
    u64 count = perft(P,O,depth);
    printf("{\"depth\":%d,\"count\":%llu",depth,(unsigned long long)count);
  } else if (!strcmp(cmd,"mirror")) {
    int holds = mirror(P,O,white_turn,!strcmp(direction,"lower"),threshold,fuel);
    printf("{\"direction\":\"%s\",\"threshold\":%d,\"holds\":%s,\"fuel\":%d,\"order\":\"row-major\",\"noTT\":true,\"scoring\":\"white-minus-black\"",direction,threshold,holds ? "true" : "false",fuel);
  } else if (!strcmp(cmd,"solve")) {
    int result = solve(P,O,-64,64);
    printf("{\"value\":%d,\"scoring\":\"white-minus-black\"",white_turn ? result : -result);
  } else {
    int lower = !strcmp(direction,"lower"), alpha, beta;
    if (white_turn) { alpha = lower ? threshold - 1 : threshold; beta = alpha + 1; }
    else { alpha = lower ? -threshold : -threshold - 1; beta = alpha + 1; }
    int result = solve(P,O,alpha,beta);
    int raw = white_turn ? result : -result;
    int holds = lower ? raw >= threshold : raw <= threshold;
    printf("{\"direction\":\"%s\",\"threshold\":%d,\"holds\":%s,\"scoring\":\"white-minus-black\"",direction,threshold,holds ? "true" : "false");
  }
  if(save_tt && checkpoint(save_tt,1,ttbits)) { free(tt); return 2; }
  printf(",\"deep_order\":%d", DEEPORD);
  printf(",\"nodes\":%llu,\"tt_hits\":%llu,\"tt_collisions\":%llu,\"tt_bits\":%d,\"tt_bytes\":%zu,\"cpu_seconds\":%.6f}\n",
         (unsigned long long)nodes,(unsigned long long)tt_hits,(unsigned long long)tt_collisions,
         ttbits,tt ? ttn * sizeof(Bucket) : 0,(double)(clock()-start)/CLOCKS_PER_SEC);
  free(tt); return 0;
}
