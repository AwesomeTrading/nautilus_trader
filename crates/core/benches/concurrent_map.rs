// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// -------------------------------------------------------------------------------------------------

//! Benchmarks comparing `Arc<DashMap>`, `Arc<RwLock<AHashMap>>`, and `Arc<ArcSwap<AHashMap>>`
//! for read-heavy concurrent access patterns.
//!
//! Hardware: Apple M4 Pro (8P+4E cores), 24 GB RAM, macOS, rustc 1.94.0.
//!
//! Results (10k reads/thread, barrier-synced, String keys, u64 values):
//!
//! ```text
//! Single-threaded read (per-lookup, no contention)
//! ┌──────────┬──────────┬──────────┬──────────┐
//! │ Map size │ DashMap  │ RwLock   │ ArcSwap  │
//! ├──────────┼──────────┼──────────┼──────────┤
//! │ 100      │ 18.1 ns  │  7.8 ns  │  8.8 ns  │
//! │ 1000     │ 31.6 ns  │  8.2 ns  │ 11.2 ns  │
//! └──────────┴──────────┴──────────┴──────────┘
//!
//! Concurrent reads (100 entries)
//! ┌──────────┬──────────┬──────────┬──────────┐
//! │ Threads  │ DashMap  │ RwLock   │ ArcSwap  │
//! ├──────────┼──────────┼──────────┼──────────┤
//! │  4       │  690 us  │  2.4 ms  │  453 us  │
//! │  8       │  1.4 ms  │  7.3 ms  │  243 us  │
//! │ 16       │  3.6 ms  │ 35.9 ms  │  793 us  │
//! └──────────┴──────────┴──────────┴──────────┘
//!
//! Write-once read-many (1000 entries)
//! ┌──────────┬──────────┬──────────┬──────────┐
//! │ Threads  │ DashMap  │ RwLock   │ ArcSwap  │
//! ├──────────┼──────────┼──────────┼──────────┤
//! │  4       │  550 us  │  2.1 ms  │  141 us  │
//! │  8       │  2.5 ms  │ 10.2 ms  │  350 us  │
//! │ 16       │  2.0 ms  │ 43.4 ms  │  430 us  │
//! └──────────┴──────────┴──────────┴──────────┘
//! ```
//!
//! NOTE: macOS `pthread_rwlock` uses a fair scheduling policy that causes reader-to-reader
//! contention at high thread counts. Linux futex-based RwLock does not have this property.
//! Run on both platforms before drawing conclusions for production (Linux) deployments.

use std::{
    hint::black_box,
    sync::{Arc, Barrier, RwLock},
};

use ahash::AHashMap;
use arc_swap::ArcSwap;
use criterion::{BenchmarkId, Criterion, criterion_group, criterion_main};
use dashmap::DashMap;

const MAP_SIZES: [usize; 2] = [100, 1_000];
const THREAD_COUNTS: [usize; 4] = [1, 4, 8, 16];
const READS_PER_THREAD: usize = 10_000;
const WRITES_PER_CYCLE: usize = 10;

fn make_keys(n: usize) -> Vec<String> {
    (0..n).map(|i| format!("BTCUSDT.BINANCE-{i:04}")).collect()
}

fn populated_dashmap(keys: &[String]) -> Arc<DashMap<String, u64>> {
    let map = DashMap::with_capacity(keys.len());
    for (i, key) in keys.iter().enumerate() {
        map.insert(key.clone(), i as u64);
    }
    Arc::new(map)
}

fn populated_rwlock(keys: &[String]) -> Arc<RwLock<AHashMap<String, u64>>> {
    let mut map = AHashMap::with_capacity(keys.len());
    for (i, key) in keys.iter().enumerate() {
        map.insert(key.clone(), i as u64);
    }
    Arc::new(RwLock::new(map))
}

fn populated_arcswap(keys: &[String]) -> Arc<ArcSwap<AHashMap<String, u64>>> {
    let mut map = AHashMap::with_capacity(keys.len());
    for (i, key) in keys.iter().enumerate() {
        map.insert(key.clone(), i as u64);
    }
    Arc::new(ArcSwap::from_pointee(map))
}

fn bench_single_thread_read(c: &mut Criterion) {
    let mut group = c.benchmark_group("single_thread_read");

    for &size in &MAP_SIZES {
        let keys = make_keys(size);

        let dash = populated_dashmap(&keys);
        group.bench_with_input(BenchmarkId::new("DashMap", size), &size, |b, _| {
            let mut idx = 0usize;
            b.iter(|| {
                let key = &keys[idx % keys.len()];
                let val = dash.get(key).map(|r| *r.value());
                black_box(val);
                idx = idx.wrapping_add(1);
            });
        });

        let rwl = populated_rwlock(&keys);
        group.bench_with_input(BenchmarkId::new("RwLockAHashMap", size), &size, |b, _| {
            let mut idx = 0usize;
            b.iter(|| {
                let key = &keys[idx % keys.len()];
                let guard = rwl.read().unwrap();
                let val = guard.get(key).copied();
                drop(guard);
                black_box(val);
                idx = idx.wrapping_add(1);
            });
        });

        let swp = populated_arcswap(&keys);
        group.bench_with_input(BenchmarkId::new("ArcSwapAHashMap", size), &size, |b, _| {
            let mut idx = 0usize;
            b.iter(|| {
                let key = &keys[idx % keys.len()];
                let guard = swp.load();
                let val = guard.get(key).copied();
                drop(guard);
                black_box(val);
                idx = idx.wrapping_add(1);
            });
        });
    }
    group.finish();
}

fn bench_concurrent_reads(c: &mut Criterion) {
    let mut group = c.benchmark_group("concurrent_reads");

    for &size in &MAP_SIZES {
        let keys = make_keys(size);

        for &threads in &THREAD_COUNTS {
            let param = format!("{size}_entries/{threads}_threads");

            let dash = populated_dashmap(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(BenchmarkId::new("DashMap", &param), &threads, |b, _| {
                b.iter(|| {
                    let barrier = Arc::new(Barrier::new(threads));
                    std::thread::scope(|s| {
                        for t in 0..threads {
                            let map = Arc::clone(&dash);
                            let ks = Arc::clone(&keys_arc);
                            let bar = Arc::clone(&barrier);
                            s.spawn(move || {
                                bar.wait();
                                for i in 0..READS_PER_THREAD {
                                    let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                    black_box(map.get(key).map(|r| *r.value()));
                                }
                            });
                        }
                    });
                });
            });

            let rwl = populated_rwlock(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(
                BenchmarkId::new("RwLockAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            for t in 0..threads {
                                let map = Arc::clone(&rwl);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.read().unwrap();
                                        black_box(guard.get(key).copied());
                                        drop(guard);
                                    }
                                });
                            }
                        });
                    });
                },
            );

            let swp = populated_arcswap(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(
                BenchmarkId::new("ArcSwapAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            for t in 0..threads {
                                let map = Arc::clone(&swp);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.load();
                                        black_box(guard.get(key).copied());
                                    }
                                });
                            }
                        });
                    });
                },
            );
        }
    }
    group.finish();
}

fn bench_read_heavy_mixed(c: &mut Criterion) {
    let mut group = c.benchmark_group("read_heavy_mixed");

    for &size in &MAP_SIZES {
        let keys = make_keys(size);
        let write_keys: Vec<String> = (0..WRITES_PER_CYCLE)
            .map(|i| format!("WRITE-KEY-{i:04}"))
            .collect();

        for &threads in &THREAD_COUNTS {
            if threads < 2 {
                continue;
            }
            let readers = threads - 1;
            let param = format!("{size}_entries/{readers}r_1w");

            let dash = populated_dashmap(&keys);
            let keys_arc = Arc::new(keys.clone());
            let wk_arc = Arc::new(write_keys.clone());
            group.bench_with_input(BenchmarkId::new("DashMap", &param), &threads, |b, _| {
                b.iter(|| {
                    let barrier = Arc::new(Barrier::new(threads));
                    std::thread::scope(|s| {
                        let map = Arc::clone(&dash);
                        let wk = Arc::clone(&wk_arc);
                        let bar = Arc::clone(&barrier);
                        s.spawn(move || {
                            bar.wait();
                            for (i, key) in wk.iter().enumerate() {
                                map.insert(key.clone(), (size + i) as u64);
                            }
                            for key in wk.iter() {
                                map.remove(key);
                            }
                        });

                        for t in 0..readers {
                            let map = Arc::clone(&dash);
                            let ks = Arc::clone(&keys_arc);
                            let bar = Arc::clone(&barrier);
                            s.spawn(move || {
                                bar.wait();
                                for i in 0..READS_PER_THREAD {
                                    let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                    black_box(map.get(key).map(|r| *r.value()));
                                }
                            });
                        }
                    });
                });
            });

            let rwl = populated_rwlock(&keys);
            let keys_arc = Arc::new(keys.clone());
            let wk_arc = Arc::new(write_keys.clone());
            group.bench_with_input(
                BenchmarkId::new("RwLockAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            let map = Arc::clone(&rwl);
                            let wk = Arc::clone(&wk_arc);
                            let bar = Arc::clone(&barrier);
                            s.spawn(move || {
                                bar.wait();
                                for (i, key) in wk.iter().enumerate() {
                                    let mut guard = map.write().unwrap();
                                    guard.insert(key.clone(), (size + i) as u64);
                                    drop(guard);
                                }
                                for key in wk.iter() {
                                    let mut guard = map.write().unwrap();
                                    guard.remove(key);
                                    drop(guard);
                                }
                            });

                            for t in 0..readers {
                                let map = Arc::clone(&rwl);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.read().unwrap();
                                        black_box(guard.get(key).copied());
                                        drop(guard);
                                    }
                                });
                            }
                        });
                    });
                },
            );

            let swp = populated_arcswap(&keys);
            let keys_arc = Arc::new(keys.clone());
            let wk_arc = Arc::new(write_keys.clone());
            group.bench_with_input(
                BenchmarkId::new("ArcSwapAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            let map = Arc::clone(&swp);
                            let wk = Arc::clone(&wk_arc);
                            let bar = Arc::clone(&barrier);
                            s.spawn(move || {
                                bar.wait();
                                let mut snapshot = AHashMap::clone(&map.load());
                                for (i, key) in wk.iter().enumerate() {
                                    snapshot.insert(key.clone(), (size + i) as u64);
                                }
                                map.store(Arc::new(snapshot));

                                let mut snapshot = AHashMap::clone(&map.load());
                                for key in wk.iter() {
                                    snapshot.remove(key);
                                }
                                map.store(Arc::new(snapshot));
                            });

                            for t in 0..readers {
                                let map = Arc::clone(&swp);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.load();
                                        black_box(guard.get(key).copied());
                                    }
                                });
                            }
                        });
                    });
                },
            );
        }
    }
    group.finish();
}

fn bench_write_once_read_many(c: &mut Criterion) {
    let mut group = c.benchmark_group("write_once_read_many");

    for &size in &MAP_SIZES {
        let keys = make_keys(size);

        for &threads in &THREAD_COUNTS {
            let param = format!("{size}_entries/{threads}_threads");

            let dash = populated_dashmap(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(BenchmarkId::new("DashMap", &param), &threads, |b, _| {
                b.iter(|| {
                    let barrier = Arc::new(Barrier::new(threads));
                    std::thread::scope(|s| {
                        for t in 0..threads {
                            let map = Arc::clone(&dash);
                            let ks = Arc::clone(&keys_arc);
                            let bar = Arc::clone(&barrier);
                            s.spawn(move || {
                                bar.wait();
                                for i in 0..READS_PER_THREAD {
                                    let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                    black_box(map.get(key).map(|r| *r.value()));
                                }
                            });
                        }
                    });
                });
            });

            let rwl = populated_rwlock(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(
                BenchmarkId::new("RwLockAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            for t in 0..threads {
                                let map = Arc::clone(&rwl);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.read().unwrap();
                                        black_box(guard.get(key).copied());
                                        drop(guard);
                                    }
                                });
                            }
                        });
                    });
                },
            );

            let swp = populated_arcswap(&keys);
            let keys_arc = Arc::new(keys.clone());
            group.bench_with_input(
                BenchmarkId::new("ArcSwapAHashMap", &param),
                &threads,
                |b, _| {
                    b.iter(|| {
                        let barrier = Arc::new(Barrier::new(threads));
                        std::thread::scope(|s| {
                            for t in 0..threads {
                                let map = Arc::clone(&swp);
                                let ks = Arc::clone(&keys_arc);
                                let bar = Arc::clone(&barrier);
                                s.spawn(move || {
                                    bar.wait();
                                    for i in 0..READS_PER_THREAD {
                                        let key = &ks[(t * READS_PER_THREAD + i) % ks.len()];
                                        let guard = map.load();
                                        black_box(guard.get(key).copied());
                                    }
                                });
                            }
                        });
                    });
                },
            );
        }
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_single_thread_read,
    bench_concurrent_reads,
    bench_read_heavy_mixed,
    bench_write_once_read_many,
);
criterion_main!(benches);
