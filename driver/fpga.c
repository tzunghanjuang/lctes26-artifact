//
// Copyright (c) 2017, Intel Corporation
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// Redistributions of source code must retain the above copyright notice, this
// list of conditions and the following disclaimer.
//
// Redistributions in binary form must reproduce the above copyright notice,
// this list of conditions and the following disclaimer in the documentation
// and/or other materials provided with the distribution.
//
// Neither the name of the Intel Corporation nor the names of its contributors
// may be used to endorse or promote products derived from this software
// without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

#include "fpga.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <uuid/uuid.h>
#include <opae/mpf/mpf.h>

int
probe_for_ase (void)
{
  fpga_result r = FPGA_OK;
  uint16_t device_id = 0;

  // Connect to the FPGA management engine
  fpga_properties filter = NULL;
  fpgaGetProperties(NULL, &filter);
  fpgaPropertiesSetObjectType(filter, FPGA_DEVICE);

  // Connecting to one is sufficient to find ASE.
  uint32_t num_matches = 1;
  fpga_token fme_token;
  fpgaEnumerate(&filter, 1, &fme_token, 1, &num_matches);
  if (0 != num_matches)
    {
      // Retrieve the device ID of the FME
      fpgaGetProperties(fme_token, &filter);
      r = fpgaPropertiesGetDeviceID(filter, &device_id);
      fpgaDestroyToken(&fme_token);
    }
  fpgaDestroyProperties(&filter);

  // ASE's device ID is 0xa5e
  return ((FPGA_OK == r) && (0xa5e == device_id));
}

fpga_result
find_and_open_fpga (const char *accel_uuid, fpga_handle *accel_handle)
{
  fpga_result r;
  fpga_token* tokens = NULL;
  uint32_t max_tokens = 0;
  uint32_t num_matches = 0;

  fpga_properties filter = NULL;
  fpgaGetProperties(NULL, &filter);
  fpgaPropertiesSetObjectType(filter, FPGA_ACCELERATOR);

  fpga_guid guid;
  uuid_parse(accel_uuid, guid);
  fpgaPropertiesSetGUID(filter, guid);

  fpgaEnumerate(&filter, 1, NULL, 0, &max_tokens);
  if (0 == max_tokens)
    {
      fprintf(stderr, "FPGA with accelerator uuid %s not found!\n", accel_uuid);
      r = FPGA_NOT_FOUND;
      goto done;
    }

  // Now that the number of matches is known, allocate a token vector
  // large enough to hold them.
  tokens = malloc(max_tokens * sizeof (fpga_token));
  if (NULL == tokens)
    {
      r = FPGA_NO_MEMORY;
      goto done;
    }

  // Enumerate and get the tokens
  fpgaEnumerate(&filter, 1, tokens, max_tokens, &num_matches);

  // Try to open a matching accelerator.  fpgaOpen() will fail if the
  // accelerator is already in use.
  fpga_token accel_token;
  fpga_handle handle;
  r = FPGA_NOT_FOUND;
  for (uint32_t i = 0; i < num_matches; i++)
    {
      accel_token = tokens[i];
      r = fpgaOpen(accel_token, &handle, 0);
      if (FPGA_OK == r) break;
    }

  if (FPGA_OK != r)
    {
      fprintf(stderr, "No accelerator available with uuid %s\n", accel_uuid);
      goto done;
    }

  fpgaMapMMIO(handle, 0, NULL);
  *accel_handle = handle;

done:
  fpgaDestroyProperties(&filter);

  // Done with tokens
  for (uint32_t i = 0; i < num_matches; i++)
    fpgaDestroyToken(&tokens[i]);

  free(tokens);
  return r;
}

void
close_fpga (fpga_handle accel_handle)
{
  fpgaUnmapMMIO(accel_handle, 0);
  fpgaClose(accel_handle);
}

fpga_result
prepare_buffer (fpga_handle handle, void *buffer, uint64_t len, uint64_t *wsid)
{
  fpga_result r;
  uint64_t _wsid;
  if ((r = fpgaPrepareBuffer(handle, len, &buffer, &_wsid, FPGA_BUF_PREALLOCATED)))
    goto err_share_buffer;

  uint64_t io_addr;
  if ((r = fpgaGetIOAddress(handle, _wsid, &io_addr)))
    goto err_map_buffer_to_fpga;

  if ((r = fpgaWriteMMIO64(handle, 0, 0x00, io_addr / CL(1))))
    goto err_map_buffer_to_fpga;

  *wsid = _wsid;
  return r;

err_map_buffer_to_fpga:
  fpgaReleaseBuffer(handle, _wsid);

err_share_buffer:
  return r;
}

fpga_result
release_buffer (fpga_handle handle, uint64_t wsid)
{
  return fpgaReleaseBuffer(handle, wsid);
}

