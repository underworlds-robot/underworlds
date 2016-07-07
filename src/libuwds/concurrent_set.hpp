//
// Based on the concurrent queue by Juan Palacios juan.palacios.puyana@gmail.com

#ifndef CONCURRENT_SET_
#define CONCURRENT_SET_

#include <set>
#include <thread>
#include <mutex>
#include <condition_variable>

namespace uwds {

template <typename T>
class ConcurrentSet
{
 public:

  bool empty() 
  {
    std::unique_lock<std::mutex> mlock(mutex_);
    return _set.empty();
  }

  T pop() 
  {
    std::unique_lock<std::mutex> mlock(mutex_);
    while (_set.empty())
    {
      cond_.wait(mlock);
    }
    auto val = *_set.begin();
    _set.erase(_set.begin());
    return val;
  }

  void insert(const T& item)
  {
    std::unique_lock<std::mutex> mlock(mutex_);

    // If a node is already in the set, we remove it
    // and replace it by the new version that is more up-to-date
    if(_set.find(item) != _set.end()) { // the element is already there
        _set.erase(item);
    }

    _set.insert(item);
    mlock.unlock();
    cond_.notify_one();
  }

  void insert(const T&& item)
  {
    std::unique_lock<std::mutex> mlock(mutex_);
    
    // If a node is already in the set, we remove it
    // and replace it by the new version that is more up-to-date
    if(_set.find(item) != _set.end()) { // the element is already there
        _set.erase(item);
    }

    _set.insert(std::move(item));
    mlock.unlock();
    cond_.notify_one();
  }

  ConcurrentSet()=default;
  ConcurrentSet(const ConcurrentSet&) = delete;            // disable copying
  ConcurrentSet& operator=(const ConcurrentSet&) = delete; // disable assignment
  
 private:
  std::set<T> _set;
  std::mutex mutex_;
  std::condition_variable cond_;
};

}
#endif
