import torch
import torchvision
from torch.utils.data import Dataset, DataLoader, TensorDataset
import torch._dynamo as torchdynamo
from torch.ao.quantization.quantize_pt2e import convert_pt2e, prepare_pt2e
import shir

transform = torchvision.models.ResNet18_Weights.IMAGENET1K_V1.transforms()

batch_size = 64

model = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
model.eval()

PROBLEM_SIZE_N = 128

_qex = torch.rand(PROBLEM_SIZE_N, 3, 224, 224)
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
  model = torch.compile(model, backend=shir.backend2.resnet_compiler)

  model(example_inputs[0])
