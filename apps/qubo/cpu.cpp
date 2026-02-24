#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <climits>
#include <sys/time.h>
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

// ---- Parameters ----
static const int WORD_BITS = 32;

// Bit-pack: variable i is stored at word (i>>5), bit (i&31)
static inline int get_bit(const std::vector<uint32_t>& X, int i) {
  return (int)((X[i >> 5] >> (i & 31)) & 1u);
}
static inline void flip_bit(std::vector<uint32_t>& X, int i) {
  X[i >> 5] ^= (1u << (i & 31));
}

static inline uint32_t hash_u32(uint32_t x) {
  x = ((x >> 16) ^ x) * 0x45d9f3bU;
  x = ((x >> 16) ^ x) * 0x45d9f3bU;
  x = (x >> 16) ^ x;
  return x;
}

static long long Energy(int N, 
                        const std::vector<int>& Bdiag, 
                        const std::vector<uint32_t>& X, 
                        const std::vector<int16_t>& Qupper) {
  long long e = 0;
  for (int i = 0; i < N; i++) {
    const int xi = get_bit(X, i);
    e += (long long)Bdiag[(size_t)i] * xi;
    for (int j = i + 1; j < N; j++) {
      const int xj = get_bit(X, j);
      e += (long long)Qupper[(size_t)i * (size_t)N + (size_t)j] * xi * xj;
    }
  }
  return e;
}

static inline void apply_flip(int N, 
                              const std::vector<int16_t>& W, 
                              int flip, int flipvalue_before, 
                              std::vector<uint32_t>& X, 
                              std::vector<int>& DeltaE, 
                              long long& CurrentE) {
  for (int v = 0; v < N; v++) {
    const int xv = get_bit(X, v);
    const int sgn = 1 - 2 * (flipvalue_before ^ xv);
    DeltaE[(size_t)v] += sgn * (int)W[(size_t)flip * (size_t)N + (size_t)v];
  }

  CurrentE += (long long)DeltaE[(size_t)flip];
  DeltaE[(size_t)flip] = -DeltaE[(size_t)flip];
  flip_bit(X, flip);
}

static void randomize_cpu(int N,
                          const std::vector<int>& Bdiag, 
                          const std::vector<int16_t>& W, 
                          std::vector<int>& DeltaE, 
                          long long& CurrentE, 
                          std::vector<uint32_t>& X, 
                          int step) {

  for (int i = 0; i < N; i++) {
    const uint32_t r = hash_u32((uint32_t)(i + step));
    const int want = (int)(r & 1u);
    if (want) {
      //apply_flip(W, i, /*flipvalue_before=*/0, X, DeltaE, CurrentE);
      apply_flip(N, W, i, get_bit(X, i), X, DeltaE, CurrentE);
    }
  }
}

static void search_cpu(int N, 
                       const std::vector<int16_t>& W, 
                       std::vector<int>& DeltaE, 
                       long long& CurrentE, 
                       std::vector<uint32_t>& X) {
  bool flag = false;
  do {
    int min_val = INT_MAX;
    int flip = -1;
    for (int v = 0; v < N; v++) {
      if (DeltaE[(size_t)v] < min_val) {
        min_val = DeltaE[(size_t)v];
        flip = v;
      }
    }
    flag = min_val >= 0 || flip < 0;
    // if (min_val >= 0 || flip < 0) {
    //   break;
    // }
    if (!flag) {
      const int flipvalue_before = get_bit(X, flip);
      apply_flip(N, W, flip, flipvalue_before, X, DeltaE, CurrentE);
    }
  } while (!flag);
}

static void print_solution_bits(int N, const std::vector<uint32_t>& X) {
  for (int i = 0; i < N; i++) {
    std::cout << get_bit(X, i);
  }
  std::cout << '\n';
}

int main(int argc, char** argv) {

  if (argc < 2 || argc > 3) {
    std::fprintf(stderr, "Usage:\n\t./cpu_qubo input.csv [STEP]\n\t(STEP default: 1000)\n");
    return 1;
  }
  
  // Get STEP from command line (optional)
  int STEP = 1000; // default
  if (argc == 3) {
    STEP = std::atoi(argv[2]);
  }    

  // Read N from CSV
  int N = 0;
  std::ifstream ifs(argv[1]);
  {

    std::string s;

    // ---- First line: read N ----
    if (!std::getline(ifs, s)) {
        std::fprintf(stderr, "Failed to read first line\n");
        return 1;
    }

    std::sscanf(s.c_str(), "%d", &N);

    if (N <= 0) {
        std::fprintf(stderr, "Invalid N in CSV\n");
        return 1;
    }  
  }

  // Read Q matrix
  std::vector<int16_t> Q((size_t)N * (size_t)N, 0);
  {
    std::string s;
    int line = 1;
    while (ifs && std::getline(ifs, s)) {
      std::istringstream iss(s);
      std::string tmp;
      int word = line; // upper-triangle
      while (std::getline(iss, tmp, ',')) {
        int v = 0;
        std::sscanf(tmp.c_str(), "%d", &v);
        Q[(size_t)(line - 1) * (size_t)N + (size_t)(word - 1)] = (int16_t)v;
        if (line < word) {
          Q[(size_t)(word - 1) * (size_t)N + (size_t)(line - 1)] =
	    Q[(size_t)(line - 1) * (size_t)N + (size_t)(word - 1)];
        }
        word++;
      }
      line++;
    }
  }


  // Extract diagonal to B, and zero diagonal in W (same as host.cu)
  std::vector<int> Bdiag((size_t)N, 0);
  for (int i = 0; i < N; i++) {
    Bdiag[(size_t)i] = (int)Q[(size_t)i * (size_t)N + (size_t)i];
    Q[(size_t)i * (size_t)N + (size_t)i] = 0;
  }

  std::cout << argv[1] << std::endl;
  std::printf("N %d, STEP %d\n", N, STEP);

  timeval t1, t2;
  gettimeofday(&t1, nullptr);

  int N_WORDS = (N + WORD_BITS - 1) / WORD_BITS;  
  std::vector<uint32_t> X((size_t)N_WORDS, 0u), BestX((size_t)N_WORDS, 0u);
  std::vector<int> DeltaE((size_t)N, 0);
  long long CurrentE = 0, BestE = 0;

  X.assign((size_t)N_WORDS, 0u);

  DeltaE.resize((size_t)N);
  for (int i = 0; i < N; i++) {
    DeltaE[(size_t)i] = Bdiag[(size_t)i];
  }
  CurrentE = 0;

  for (uint32_t step = 0; step < (uint32_t)STEP; step++) {
    randomize_cpu(N, Bdiag, Q, DeltaE, CurrentE, X, step);
    search_cpu(N, Q, DeltaE, CurrentE, X);
    if (CurrentE < BestE) {
      BestX = X;
      BestE = CurrentE;
    }
  }

  long long E = Energy(N, Bdiag, BestX, Q);
  std::printf("%lld (verification: %lld)\n", BestE, E);

  std::printf("Solution bits (N=%d):\n", N);
  print_solution_bits(N, BestX);

  gettimeofday(&t2, nullptr);
  std::printf("time = %lf sec.\n", (t2.tv_sec - t1.tv_sec) + (t2.tv_usec - t1.tv_usec) * 1.0E-6);

  return 0;
}
