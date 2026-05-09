# model and weight loading code based on gh:miladlink/TinyYoloV2
#
# the link for weights seems to be dead, but wayback machine seems to have
# saved a copy of it (around 60 MB):
#   https://pjreddie.com/media/files/yolov2-tiny-voc.weights

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import torchvision
from torchvision.transforms import v2
from torch.utils.data import Dataset, DataLoader, TensorDataset
import torch._dynamo as torchdynamo
from torch.ao.quantization.quantize_pt2e import convert_pt2e, prepare_pt2e
import shir

def load_conv_bn(buf, start, conv_layer, bn_layer):
  num_w = conv_layer.weight.numel()
  num_b = bn_layer.bias.numel()

  bn_layer.bias.data.copy_(torch.from_numpy(buf[start:start + num_b]))
  start += num_b
  bn_layer.weight.data.copy_(torch.from_numpy(buf[start:start + num_b]))
  start += num_b
  bn_layer.running_mean.data.copy_(torch.from_numpy(buf[start:start + num_b]))
  start += num_b
  bn_layer.running_var.data.copy_(torch.from_numpy(buf[start:start + num_b]))
  start += num_b

  conv_layer.weight.data.copy_(torch.from_numpy(buf[start:start + num_w]).reshape_as(conv_layer.weight))
  start += num_w

  return start

def load_conv(buf, start, conv_layer):
  num_w = conv_layer.weight.numel()
  num_b = conv_layer.bias.numel()

  conv_layer.bias.data.copy_(torch.from_numpy(buf[start:start + num_b]))
  start += num_b
  conv_layer.weight.data.copy_(torch.from_numpy(buf[start:start + num_w]).reshape_as(conv_layer.weight))
  start += num_w

  return start

class TinyYoloV2(nn.Module):
  def __init__(self):
    super(TinyYoloV2, self).__init__()

    self.conv1 = nn.Conv2d(3, 16, 3, 1, 1, bias=False)
    self.bn1 = nn.BatchNorm2d(16)

    self.conv2 = nn.Conv2d(16, 32, 3, 1, 1, bias=False)
    self.bn2 = nn.BatchNorm2d(32)

    self.conv3 = nn.Conv2d(32, 64, 3, 1, 1, bias=False)
    self.bn3 = nn.BatchNorm2d(64)

    self.conv4 = nn.Conv2d(64, 128, 3, 1, 1, bias=False)
    self.bn4 = nn.BatchNorm2d(128)

    self.conv5 = nn.Conv2d(128, 256, 3, 1, 1, bias=False)
    self.bn5 = nn.BatchNorm2d(256)

    self.conv6 = nn.Conv2d(256, 512, 3, 1, 1, bias=False)
    self.bn6 = nn.BatchNorm2d(512)

    self.conv7 = nn.Conv2d(512, 1024, 3, 1, 1, bias=False)
    self.bn7 = nn.BatchNorm2d(1024)

    self.conv8 = nn.Conv2d(1024, 1024, 3, 1, 1, bias=False)
    self.bn8 = nn.BatchNorm2d(1024)

    # 125 comes from (5 + #classes) * #anchors = (5 + 20) * 5
    self.output = nn.Conv2d(1024, 125, 1, 1, 0)

  def forward(self, x):
    x = F.max_pool2d(F.leaky_relu(self.bn1(self.conv1(x)), 0.1), 2)
    x = F.max_pool2d(F.leaky_relu(self.bn2(self.conv2(x)), 0.1), 2)
    x = F.max_pool2d(F.leaky_relu(self.bn3(self.conv3(x)), 0.1), 2)
    x = F.max_pool2d(F.leaky_relu(self.bn4(self.conv4(x)), 0.1), 2)
    x = F.max_pool2d(F.leaky_relu(self.bn5(self.conv5(x)), 0.1), 2)
    x = F.max_pool2d(F.pad(F.leaky_relu(self.bn6(self.conv6(x)), 0.1), (0, 1, 0, 1), mode='replicate'), 2, 1)
    x = F.leaky_relu(self.bn7(self.conv7(x)), 0.1)
    x = F.leaky_relu(self.bn8(self.conv8(x)), 0.1)
    x = self.output(x)
    return x

  def load_weights(self, file):
    buf = np.fromfile(file, dtype=np.float32)

    # apparently the first four entries are actually int32 fields
    # skip over those
    start = 4

    start = load_conv_bn(buf, start, self.conv1, self.bn1)
    start = load_conv_bn(buf, start, self.conv2, self.bn2)
    start = load_conv_bn(buf, start, self.conv3, self.bn3)
    start = load_conv_bn(buf, start, self.conv4, self.bn4)
    start = load_conv_bn(buf, start, self.conv5, self.bn5)
    start = load_conv_bn(buf, start, self.conv6, self.bn6)
    start = load_conv_bn(buf, start, self.conv7, self.bn7)
    start = load_conv_bn(buf, start, self.conv8, self.bn8)
    load_conv(buf, start, self.output)

def yolo(x):
  n, _, h, w = x.shape

  # recover the anchor dimension
  x = x.view(n, 5, -1, h, w).permute(0, 1, 3, 4, 2)
  anchors = torch.tensor([
    [1.08, 1.19],
    [3.42, 4.41],
    [6.63, 11.38],
    [9.42, 5.11],
    [16.62, 10.52],
  ])
  range_y, range_x = torch.meshgrid(
    torch.arange(h),
    torch.arange(w),
  )

  x = torch.cat([
    (x[:, :, :, :, 0:1].sigmoid() + range_x[None, None, :, :, None]) / w,
    (x[:, :, :, :, 1:2].sigmoid() + range_y[None, None, :, :, None]) / h,
    (x[:, :, :, :, 2:3].exp() * anchors[:, 0][None, :, None, None, None]) / w,
    (x[:, :, :, :, 3:4].exp() * anchors[:, 1][None, :, None, None, None]) / h,
    x[:, :, :, :, 4:5].sigmoid(),
    x[:, :, :, :, 5:].softmax(-1),
  ], -1)
  return x

def show_images_with_boxes(input_tensor, output_tensor):
  from PIL import ImageDraw, Image
  to_img = torchvision.transforms.ToPILImage()
  for img, predictions in zip(input_tensor, output_tensor):
    img = to_img(img)
    if 0 in predictions.shape: # empty tensor
      display(img)
      continue
    confidences = predictions[..., 4].flatten()
    boxes = (
      predictions[..., :4].contiguous().view(-1, 4)
    )  # only take first four features: x0, y0, w, h
    classes = predictions[..., 5:].contiguous().view(boxes.shape[0], -1)
    boxes[:, ::2] *= img.width
    boxes[:, 1::2] *= img.height
    boxes = (torch.stack([
                boxes[:, 0] - boxes[:, 2] / 2,
                boxes[:, 1] - boxes[:, 3] / 2,
                boxes[:, 0] + boxes[:, 2] / 2,
                boxes[:, 1] + boxes[:, 3] / 2,
    ], -1).cpu().to(torch.int32).numpy())
    for box, confidence, class_ in zip(boxes, confidences, classes):
      if confidence < 0.01:
        continue # don't show boxes with very low confidence
      # make sure the box fits within the picture:
      box = [
        max(0, int(box[0])),
        max(0, int(box[1])),
        min(img.width - 1, int(box[2])),
        min(img.height - 1, int(box[3])),
      ]
      # the 20 softmax probabilities are given as features 6-25
      if class_.shape[0] == 1:
        idx = int(class_.item())
      else:
        idx = int(torch.max(class_, 0)[1].item())
      try:
        class_ = CLASSES[idx]  # the first index of torch.max is the argmax.
      except IndexError: # if the class index does not exist, don't draw anything:
        continue

      
      color = (  # green color when confident, red color when not confident.
        int((1 - (confidence.item())**0.8 ) * 255),
        int((confidence.item())**0.8 * 255),
        0,
      )
      draw = ImageDraw.Draw(img)
      draw.rectangle(box, outline=color)
      draw.text(box[:2], class_, fill=color)

    img.show()

def filter_boxes(output_tensor, threshold):
  b, a, h, w, c = output_tensor.shape
  x = output_tensor.contiguous().view(b, a * h * w, c)

  boxes = x[:, :, 0:4]
  confidence = x[:, :, 4]
  scores, idx = torch.max(x[:, :, 5:], -1)
  idx = idx.float()
  scores = scores * confidence
  mask = scores > threshold

  filtered = []
  for c, s, i, m in zip(boxes, scores, idx, mask):
    if m.any():
      detected = torch.cat([c[m, :], s[m, None], i[m, None]], -1)
    else:
      detected = torch.zeros((0, 6), dtype=x.dtype, device=x.device)
    filtered.append(detected)
  return filtered

def iou(bboxes1, bboxes2):
  """ calculate iou between each bbox in `bboxes1` with each bbox in `bboxes2`"""
  px, py, pw, ph = bboxes1[...,:4].reshape(-1, 4).split(1, -1)
  lx, ly, lw, lh = bboxes2[...,:4].reshape(-1, 4).split(1, -1)
  px1, py1, px2, py2 = px - 0.5 * pw, py - 0.5 * ph, px + 0.5 * pw, py + 0.5 * ph
  lx1, ly1, lx2, ly2 = lx - 0.5 * lw, ly - 0.5 * lh, lx + 0.5 * lw, ly + 0.5 * lh
  zero = torch.tensor(0.0, dtype=px1.dtype, device=px1.device)
  dx = torch.max(torch.min(px2, lx2.T) - torch.max(px1, lx1.T), zero)
  dy = torch.max(torch.min(py2, ly2.T) - torch.max(py1, ly1.T), zero)
  intersections = dx * dy
  pa = (px2 - px1) * (py2 - py1) # area
  la = (lx2 - lx1) * (ly2 - ly1) # area
  unions = (pa + la.T) - intersections
  ious = (intersections/unions).reshape(*bboxes1.shape[:-1], *bboxes2.shape[:-1])
  
  return ious

def nms(filtered_tensor, threshold):
  result = []
  for x in filtered_tensor:
    # Sort coordinates by descending confidence
    scores, order = x[:, 4].sort(0, descending=True)
    x = x[order]
    ious = iou(x,x) # get ious between each bbox in x

    # Filter based on iou
    keep = (ious > threshold).long().triu(1).sum(0, keepdim=True).t().expand_as(x) == 0

    result.append(x[keep].view(-1, 6).contiguous())
  return result

img_resolution = 416
batch_size = 64

transforms = v2.Compose([
  v2.ToImage(),
  v2.Resize(img_resolution),
  v2.CenterCrop(img_resolution),
  v2.ToDtype(torch.float32, scale=True),
])

CLASSES = (
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
)

training_data = torchvision.datasets.VOCSegmentation(
  root="data",
  image_set="train",
  download=False, #True,
  transform=transforms,
  target_transform=transforms,
)
train_dataloader = DataLoader(training_data, batch_size=batch_size, shuffle=False, drop_last=True)

# don't transform and dataloader this:
# the format gets in your way...
detection_data = torchvision.datasets.VOCDetection(
  root="data",
  image_set="val",
  download=False, #True,
)

def get_example_input():
  for X, _ in train_dataloader:
    return X

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

model = TinyYoloV2()
model.load_weights("data/yolov2-tiny-voc.weights")
model.eval()

PROBLEM_SIZE_N = 16

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
  model = torch.compile(model, backend=shir.backend2.yolo_compiler)

  model(example_inputs[0])
