#ifndef BUFFER_H__
#define BUFFER_H__

// this is a thin wrapper over mmap/munmap
#include <stddef.h>

void *alloc_buffer (size_t length);

void free_buffer (void *addr);

#endif /* !BUFFER_H__ */
