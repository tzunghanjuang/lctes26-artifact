import torch
import torchvision
from datasets import load_dataset
from torch.utils.data import Dataset, DataLoader, TensorDataset
import torch._dynamo as torchdynamo
from torch.ao.quantization.quantize_pt2e import convert_pt2e, prepare_pt2e
import shir

transform = torchvision.models.VGG11_Weights.IMAGENET1K_V1.transforms()
def encode(batch):
  # for whatever reason, some image are grayscale...
  # so convert it into RGB before cropping it to 224.
  batch["image"] = [transform(img.convert('RGB')) for img in batch["image"]]
  return batch

ds = load_dataset("imagenet-1k")
ds.set_transform(encode)

batch_size = 64
loss_fn = torch.nn.CrossEntropyLoss()
train_dataloader = DataLoader(ds['train'], batch_size=batch_size, shuffle=False, drop_last=True)
valid_dataloader = DataLoader(ds['validation'], batch_size=batch_size, shuffle=False, drop_last=True)
test_dataloader = DataLoader(ds['test'], batch_size=batch_size)

def get_example_input():
  for X in train_dataloader:
    return X['image']

def test_loop(dataloader, model, loss_fn):
  size = len(dataloader.dataset)
  num_batches = len(dataloader)
  test_loss, correct = 0, 0

  with torch.no_grad():
    for T in dataloader:
      X = T["image"]
      y = T["label"]
      pred = model(X)
      test_loss += loss_fn(pred, y)
      correct += (pred.argmax(1) == y).type(torch.float).sum().item()

  test_loss /= num_batches
  correct /= size
  return correct, test_loss

def time_inference(data, model):
  import time
  times = []
  with torch.no_grad():
    for X in data:
      _start = time.perf_counter_ns()
      model(X)
      _end = time.perf_counter_ns()
      times.append(_end - _start)
  return times

model = torchvision.models.vgg11(weights=torchvision.models.VGG11_Weights.IMAGENET1K_V1)
model.eval()

PROBLEM_SIZE_N = 64

_qex = get_example_input()[:PROBLEM_SIZE_N, :, :, :]
_qex = torch.concat([_qex] * ((PROBLEM_SIZE_N + (batch_size - 1)) // batch_size), axis=0)
example_inputs = (_qex,)

torchdynamo.reset()

quantizer = shir.BackendQuantizer()

with torch.no_grad():
  model = torch.export.export(model, example_inputs).module()

  model = prepare_pt2e(model, quantizer)
  model(*example_inputs)
  model = convert_pt2e(model)

  import shir.backend2
  model = torch.compile(model, backend=shir.backend2.vgg_compiler)

  model(example_inputs[0])
