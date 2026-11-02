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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>

typedef uint64_t u64;
typedef unsigned __int128 u128;

static u64 REGION;
static int ROWS = 6, COLS = 6;

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
typedef struct { u64 key; int16_t lo, hi; uint8_t empties, move; } TTE;
typedef struct { TTE deep, fresh; } Bucket;
static Bucket *tt; static u64 tt_mask;

static inline u64 hashkey(u64 P, u64 O) {
  u128 h = (u128)(P ^ 0x9e3779b97f4a7c15ULL) * 0xff51afd7ed558ccdULL;
  h ^= (u128)(O + 0xc4ceb9fe1a85ec53ULL) * 0x9e3779b97f4a7c15ULL;
  return (u64)h ^ (u64)(h >> 64);
}

/* 局面が表にあれば、その上下限を返す */
static inline TTE *tt_probe(u64 key, int empties) {
  Bucket *b = &tt[key & tt_mask];
  if (b->deep.key  == key && b->deep.empties  == (uint8_t)empties) return &b->deep;
  if (b->fresh.key == key && b->fresh.empties == (uint8_t)empties) return &b->fresh;
  return NULL;
}

static inline void tt_store(u64 key, int empties, int lo, int hi, int mv) {
  Bucket *b = &tt[key & tt_mask];
  TTE *slot;
  if (b->deep.key == key && b->deep.empties == (uint8_t)empties)      slot = &b->deep;
  else if (empties >= b->deep.empties)                                slot = &b->deep;
  else                                                                slot = &b->fresh;
  slot->key = key; slot->empties = (uint8_t)empties;
  slot->lo = (int16_t)lo; slot->hi = (int16_t)hi; slot->move = (uint8_t)mv;
}

static u64 nodes = 0;

/* ---------- 進捗表示 ----------
 * 端末へ 1 秒あたり SHOW_HZ 回ほど書き出す。
 * 書き出しは 1 回あたり約 6us かかるので、頻度を上げすぎると探索そのものが遅くなる。
 * 毎秒 20 回なら 6x6 の完全読み（410 億局面・33 分）に対して追加は 0.2 秒（0.01%）。
 * 機械の速さは事前に分からないので、最初の表示のあと間隔を自動で合わせる。 */
static int show_on = 0;
static u64 show_mask = 0;
static u64 show_total = 0;            /* 進捗率の分母。前回の実測値（0 なら率を出さない） */
static double show_hz = 20.0;
static struct timespec show_t0;
static const char *show_label = "";

static void progress(void) {
  if ((nodes & show_mask) != 0) return;
  struct timespec tv;
  clock_gettime(CLOCK_MONOTONIC, &tv);
  double el = (tv.tv_sec - show_t0.tv_sec) + (tv.tv_nsec - show_t0.tv_nsec) / 1e9;
  if (el <= 0) return;
  double rate = nodes / el;

  /* 毎秒 show_hz 回になるよう間隔を 2 のべき乗で合わせる */
  u64 want = (u64)(rate / show_hz);
  u64 m = 1; while (m < want) m <<= 1;
  if (m < 1024) m = 1024;
  show_mask = m - 1;

  fprintf(stderr, "\r%s ", show_label);
  if (show_total) {                       /* 総数の見込みがあるときだけ棒と率を出す */
    double pct = (double)nodes / (double)show_total;
    if (pct > 0.999) pct = 0.999;
    int filled = (int)(pct * 40);
    char bar[41];
    for (int i = 0; i < 40; i++) bar[i] = (i < filled) ? '#' : '.';
    bar[40] = 0;
    fprintf(stderr, "[%s] %5.1f%% ", bar, 100.0 * pct);
  }
  fprintf(stderr, "%.2f 億局面  経過 %d:%02d", nodes / 1e8,
          (int)(el / 60), (int)el % 60);
  if (show_total && nodes < show_total && rate > 0) {
    double eta = (show_total - nodes) / rate;
    fprintf(stderr, "  残り %d:%02d", (int)(eta / 60), (int)eta % 60);
  }
  fprintf(stderr, "  %.1fM/秒\033[K", rate / 1e6);
}
static int SMALL = 10;   /* この空きマス数以下は表を使わず読み切る */
static int DEEPORD = 13; /* この空きマス数以上で着手数による並べ替えをする */
static int ORDER[64], ORDER_N;

static int solve(u64 P, u64 O, int alpha, int beta, int passed);

/* 残り 10 マス以下は表を使わず読み切る */
static int solve_small(u64 P, u64 O, int alpha, int beta, int passed) {
  nodes++;
  if (show_on) progress();
  u64 moves = gen_moves(P, O);
  if (!moves) {
    if (passed) return popc(P) - popc(O);
    return -solve_small(O, P, -beta, -alpha, 1);
  }
  int best = -64;
  for (int i = 0; i < ORDER_N; i++) {
    u64 m = 1ULL << ORDER[i];
    if (!(moves & m)) continue;
    u64 f = gen_flips(P, O, m);
    int v = -solve_small(O ^ f, P ^ f ^ m, -beta, -alpha, 0);
    if (v > best) best = v;
    if (best > alpha) alpha = best;
    if (alpha >= beta) break;
  }
  return best;
}

static int solve(u64 P, u64 O, int alpha, int beta, int passed) {
  int empties = popc(~(P | O) & REGION);
  if (empties <= SMALL) return solve_small(P, O, alpha, beta, passed);

  nodes++;
  if (show_on) progress();
  u64 key = hashkey(P, O);
  int a0 = alpha, b0 = beta, ttmove = 64;
  TTE *e = tt_probe(key, empties);
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
    if (passed) return popc(P) - popc(O);
    return -solve(O, P, -beta, -alpha, 1);
  }

  /* 手を並べる：置換表の手 → 相手の着手可能数が少ない手 */
  int idx[36], sc[36], n = 0;
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
      TTE *c = tt_probe(hashkey(no_[i], np_[i]), ce);
      if (c && -c->hi >= beta) { tt_store(key, empties, -c->hi, 64, idx[i]); return -c->hi; }
    }
  }

  int best = -64, bestmv = idx[0];
  for (int i = 0; i < n; i++) {
    int v;
    if (i == 0) v = -solve(no_[i], np_[i], -beta, -alpha, 0);
    else {
      v = -solve(no_[i], np_[i], -alpha - 1, -alpha, 0);
      if (v > alpha && v < beta) v = -solve(no_[i], np_[i], -beta, -v, 0);
    }
    if (v > best) { best = v; bestmv = idx[i]; }
    if (best > alpha) alpha = best;
    if (alpha >= beta) break;
  }

  if (best <= a0)      tt_store(key, empties, -64,  best, bestmv);
  else if (best >= b0) tt_store(key, empties, best, 64,   bestmv);
  else                 tt_store(key, empties, best, best, bestmv);
  return best;
}

int main(int argc, char **argv) {
  int ttbits = (argc > 1) ? atoi(argv[1]) : 24;
  int wld    = (argc > 2 && argv[2][0] == 'w');
  { const char *q=getenv("SMALL"); if(q) SMALL=atoi(q); q=getenv("DEEPORD"); if(q) DEEPORD=atoi(q); }
  if (argc > 3) ROWS = atoi(argv[3]);
  if (argc > 4) COLS = atoi(argv[4]);

  /* 進捗表示。端末に出力しているときだけ既定で有効。
     PROGRESS=0 で止め、PROGRESS_HZ で更新頻度を変えられる。 */
  { const char *q = getenv("PROGRESS");
    show_on = q ? atoi(q) != 0 : isatty(STDERR_FILENO);
    q = getenv("PROGRESS_HZ"); if (q && atof(q) > 0) show_hz = atof(q);
    show_mask = (1ULL << 20) - 1;   /* 最初の1回まで。以後は自動で合わせる */ }
  size_t ttn = (size_t)1 << ttbits;
  tt = calloc(ttn, sizeof(Bucket));
  if (!tt) { fprintf(stderr, "置換表を確保できません\n"); return 1; }
  tt_mask = ttn - 1;
  /* 使われていないスロットが「空きマス 0 の深い局面」に見えないようにする */
  for (size_t i = 0; i < ttn; i++) { tt[i].deep.key = 1; tt[i].fresh.key = 1; }

  REGION = 0;
  for (int r = 1; r <= ROWS; r++) for (int c = 1; c <= COLS; c++) REGION |= 1ULL << (r * 8 + c);

  int w[64]; ORDER_N = 0;
  for (int r = 1; r <= ROWS; r++) for (int c = 1; c <= COLS; c++) {
    int dr = (r <= ROWS/2) ? r - 1 : ROWS - r, dc = (c <= COLS/2) ? c - 1 : COLS - c;
    int s = -(dr * 3 + dc * 3);
    if ((dr == 0 && dc == 1) || (dr == 1 && dc == 0) || (dr == 1 && dc == 1)) s -= 20;
    if (dr == 0 && dc == 0) s += 40;
    w[ORDER_N] = s; ORDER[ORDER_N] = r * 8 + c; ORDER_N++;
  }
  for (int i = 1; i < ORDER_N; i++) {
    int ki = ORDER[i], ks = w[i], j = i - 1;
    while (j >= 0 && w[j] < ks) { ORDER[j+1] = ORDER[j]; w[j+1] = w[j]; j--; }
    ORDER[j+1] = ki; w[j+1] = ks;
  }

  int r0 = ROWS/2, c0 = COLS/2;
  u64 B = (1ULL << (r0*8 + (c0+1))) | (1ULL << ((r0+1)*8 + c0));
  u64 W = (1ULL << (r0*8 + c0)) | (1ULL << ((r0+1)*8 + (c0+1)));

  printf("%dx%d オセロ %s / 置換表 2^%d バケツ = %.0f MB\n",
         ROWS, COLS, wld ? "必勝読み" : "完全読み",
         ttbits, ttn * sizeof(Bucket) / 1048576.0);
  fflush(stdout);

  /* 進捗率の分母。6x6 のみ、前回の実測値を見込みとして使う */
  show_label = wld ? "必勝読み" : "完全読み";
  if (ROWS == 6 && COLS == 6)
    show_total = wld ? 18435230807ULL : 41004075510ULL;

  struct timespec t0, t1;
  clock_gettime(CLOCK_MONOTONIC, &t0);
  show_t0 = t0;
  if (show_on) fputs("\033[?25l", stderr);   /* カーソルを消す */
  int score = wld ? solve(B, W, -1, 0, 0) : solve(B, W, -64, 64, 0);
  clock_gettime(CLOCK_MONOTONIC, &t1);

  if (show_on) fputs("\033[K\033[?25h\n", stderr);   /* 行を消してカーソルを戻す */

  double sec = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
  if (wld) printf("結果: 黒の石差は 0 以上か → %s（%s）\n",
                  score >= 0 ? "はい" : "いいえ",
                  score >= 0 ? "黒が負けない" : "白（後手）必勝");
  else     printf("結果: 黒から見た石差 = %d （%s）\n", score,
                  score > 0 ? "黒（先手）の勝ち" : score < 0 ? "白（後手）の勝ち" : "引き分け");
  printf("探索した局面数: %llu\n", (unsigned long long)nodes);
  printf("時間: %.2f 秒  速さ: %.2f M局面/秒\n", sec, nodes / sec / 1e6);
  return 0;
}
