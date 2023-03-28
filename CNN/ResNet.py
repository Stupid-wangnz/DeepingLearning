import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from zmq import Flag
from typing import Optional
import torch.optim as optim


if torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

transform = transforms.Compose(
[transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

batch_size = 4

trainset = torchvision.datasets.CIFAR10(root='E:\DeepLearning\CNN\data', train=True,
                                        download=False, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                          shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='E:\DeepLearning\CNN\data', train=False,
                                       download=False, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                         shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

class BasicBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride, downsample : Optional[nn.Module] = None) :
        super().__init__()
        self.relu = nn.ReLU()

        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.downsample = downsample

    def forward(self, x):
        _x = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        if self.downsample is not None:
            _x = self.downsample(x)

        out = self.relu(_x + out)
        
        return out

# 4 3 32 32

class ResNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False) # 3 32 32 -> 64 16 16
        self.bn1 = nn.BatchNorm2d(64)
        self.maxpool = nn.MaxPool2d(3, 2) #64 16 16 -> 64 8 8

        self.conv2_1 = BasicBlock(64, 64, 1)
        self.conv2_2 = BasicBlock(64, 128, 2,
                                downsample=nn.Sequential(
                                    nn.Conv2d(64, 128, 1, 2),
                                    nn.BatchNorm2d(128)
                                ))
        # 64 8 8 -> 128, 4, 4
        self.conv3_1 = BasicBlock(128, 128, 1)
        self.conv3_2 = BasicBlock(128, 256, 2,
                                downsample=nn.Sequential(
                                    nn.Conv2d(128, 256, 1, 2),
                                    nn.BatchNorm2d(256)
                                ))
        # 128, 4, 4 -> 256, 2, 2
        self.avgpool = nn.AvgPool2d(2,1)
        self.fc = nn.Linear(256, 10)
    def forward(self, x):       
        x = self.conv1(x)
        x = F.relu(self.bn1(x))
        x = self.maxpool(x)
        x = self.conv2_1(x)
        x= self.conv2_2(x)
        x = self.conv3_1(x)
        x = self.conv3_2(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = self.fc(x)
        x = F.softmax(x)
        return x

net = ResNet()
model = net.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

def test(loss_vector, accuracy_vector):
    model.eval()
    val_loss, correct = 0, 0
    for data, target in testloader:
        data = data.to(device)
        target = target.to(device)
        output = model(data)
        val_loss += criterion(output, target).data.item()
        pred = output.data.max(1)[1] # get the index of the max log-probability
        correct += pred.eq(target.data).cpu().sum()

    val_loss /= len(testloader)
    loss_vector.append(val_loss)

    accuracy = 100. * correct.to(torch.float32) / len(testloader.dataset)
    accuracy_vector.append(accuracy)
    
    print('\nValidation set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        val_loss, correct, len(testloader.dataset), accuracy))

def train(epoch):
    model.train()
    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        # get the inputs; data is a list of [inputs, labels]
        inputs, labels = data

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 2000 == 1999:    # print every 2000 mini-batches
            print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
            running_loss = 0.0

            
if __name__ == "__main__":

    lossv,accv=[],[]

    print("Begin training")
    for epoch in range(5):  # loop over the dataset multiple times
        train(epoch)
        test(lossv,accv)
    print('Finished Training')