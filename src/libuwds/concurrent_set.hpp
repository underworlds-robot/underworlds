//
// Based on the concurrent queue by Juan Palacios juan.palacios.puyana@gmail.com

#ifndef CONCURRENT_SET_
#define CONCURRENT_SET_

#include <chrono>
#include <set>
#include <thread>
#include <mutex>
#include <condition_variable>

#include "node.hpp"

namespace uwds {

class ConcurrentNodeSet
{
 public:

  bool empty() 
  {
    std::unique_lock<std::mutex> mlock(mutex_);
    return _set.empty();
  }

  std::weak_ptr<const Node> pop() 
  {
    std::unique_lock<std::mutex> mlock(mutex_);
    while (_set.empty())
    {
      cond_.wait(mlock);
    }
    auto val = *(_set.begin());
    _set.erase(_set.begin());
    return val;
  }

  std::cv_status pop_timed(std::weak_ptr<const Node>& val, const std::chrono::milliseconds& duration) 
  {
    std::unique_lock<std::mutex> mlock(mutex_);

    std::cv_status res;

    while (_set.empty())
    {
      res = cond_.wait_for(mlock, duration);
    }

    if (res == std::cv_status::timeout) return std::cv_status::timeout;

    val = *(_set.begin());
    _set.erase(_set.begin());
    return std::cv_status::no_timeout;
  }

  void insert(ConstNodePtr& item)
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

  void insert(ConstNodePtr&& item)
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

  ConcurrentNodeSet()=default;
  ConcurrentNodeSet(const ConcurrentNodeSet&) = delete;            // disable copying
  ConcurrentNodeSet& operator=(const ConcurrentNodeSet&) = delete; // disable assignment
  
 private:
  std::set<std::weak_ptr<const Node>> _set;
  std::mutex mutex_;
  std::condition_variable cond_;
};

}
#endif
