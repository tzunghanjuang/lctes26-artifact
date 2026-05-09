#include "buffer.h"
#include "hugetlbfs.h"

void *
alloc_buffer (size_t length)
{
  return get_huge_pages(length, GHP_DEFAULT);
}

void
free_buffer (void *addr)
{
  free_huge_pages(addr);
}
