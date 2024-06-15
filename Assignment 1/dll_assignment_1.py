# -*- coding: utf-8 -*-
"""dll_assignment_1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BEwBMX2yjXnCjUiUTaTC0-asLaC4CKZB
"""

# author: Jury Andrea D'Onofrio
from pickletools import optimize
from syslog import LOG_SYSLOG
import numpy as np
import matplotlib . pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim


def plot_polynomial(coeffs, z_range, color='b'):
    z = np.linspace(z_range[0], z_range[1], 100)
    y = np.polynomial.polynomial.polyval(z, coeffs)
    plt.plot(z, y, color)
    plt.title("Plot polynomial")
    #plt.show()


def create_dataset(w, z_range, sample_size, sigma, seed=42):
    random_state = np.random.RandomState(seed)
    z = random_state.uniform(z_range[0], z_range[1], (sample_size))
    x = np.zeros((sample_size, w.shape[0]))
 
    for i in range(sample_size):
        for j in range(w.shape[0]):
            #each row of x something as [1, z, z^2, z^3, z^4]
            x[i, j] = z[i]**j
    
    #apply vector w to the matrix x        
    y = x.dot(w)    
    if sigma > 0:
        y += random_state.normal(0.0, sigma, sample_size)
    return x, y

def visualize_data_points(x, y, label, c='b'):
    plt.figure(label)
    #x_train[:, 1] because I need all row of z in [1, z, z^2, z^3, z^4] so index 1
    plt.scatter(x[:, 1], y, s = 15, c=c)
    plt.title(label)


#init
w = np.array([0, -5, 2, 1, 0.05])
sigma = 0.5
#question 1.10 --> sample size of x_train 10
sample_size = 500
z_range = [-3, 3]


plot_polynomial(w, z_range)


#training set
#for question 1.10 x_train and y_train have sample_size = 10
x_train, y_train = create_dataset(w, z_range, sample_size, sigma, seed = 0)
print(x_train)
#validation set
x_val, y_val = create_dataset(w, z_range, sample_size, sigma, seed = 1)


#plotting
visualize_data_points(x_train, y_train, "Training set")
visualize_data_points(x_val, y_val, "Validation set", c='orange')
plt.show()


#questione 1.6
#init linear regression
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
#bias = false --> no offset in the polynomial
model = nn.Linear(5, 1, bias=False)
model = model.to(DEVICE)
loss_fn = nn.MSELoss()
#learning rate = [0.001 - 0.0012]
learning_rate = 0.0012
optimizer = optim.SGD(model.parameters(), lr = learning_rate)


#init training and validation tensors
train_x = torch.from_numpy(x_train).float().to(DEVICE)
#for question 1.10 train_y have sample_size = 10
train_y = torch.from_numpy(y_train.reshape((sample_size, 1))).float().to(DEVICE)
val_x = torch.from_numpy(x_val).float().to(DEVICE)
val_y = torch.from_numpy(y_val.reshape((sample_size, 1))).float().to(DEVICE)


plot_loss = []
plot_val_loss = []
epochs_array = []


#training loop
epochs = 1550
weights = np.zeros((epochs, 5))
for step in range(epochs):
    model.train()
    optimizer.zero_grad()
    
    y_ = model(train_x) #prediction of y
    loss = loss_fn(y_, train_y) #compute the error
    #print(f"Step {step}: train loss:{loss}")
    plot_loss.append(loss.item())

    loss.backward()
    optimizer.step()
    
    #evalution the model with the validation set
    model.eval()
    with torch.no_grad():
        y_ = model(val_x)
        val_loss = loss_fn(y_, val_y)
        plot_val_loss.append(val_loss.item())
    #print(f"Step {step}: valid loss:{val_loss}")
    epochs_array.append(step)
    
    #get coefficients, to numpy and take the list 
    weights[step] = next(model.parameters()).detach().numpy()[0]


#question 1.7
print("Initial random values of w: ", weights[0])
print("Estimate values of w: ", weights[epochs-1])


#question 1.8
fig, ax = plt.subplots()
ax.plot(epochs_array, plot_loss, '-', linewidth=2, label='Training loss')
ax.plot(epochs_array, plot_val_loss, '-', linewidth=2, label='Validation loss')
ax.hlines(y=0.6,xmin = 0, xmax = 1550, linewidth=2, color='b')
ax.legend()
plt.title("Training and validation losses over epochs")


#question 1.9 comment in the report
model.eval()
with torch.no_grad():
  y_ = model(train_x)
fig, ax = plt.subplots()
ax.plot(train_x.cpu().numpy()[:, 1], train_y.cpu().numpy(), '.', label='D\'')
ax.plot(train_x.cpu().numpy()[:, 1], y_.cpu().numpy(), '.', label='Model')
ax.legend()
plt.title("Linear regression of polynomial")


#question 1.11 bonus
fig, ax = plt.subplots()
ax.plot(epochs_array, weights[:, 0], '-', linewidth=2, label='W0')
ax.plot(epochs_array, weights[:, 1], '-', linewidth=2, label='W1')
ax.plot(epochs_array, weights[:, 2], '-', linewidth=2, label='W2')
ax.plot(epochs_array, weights[:, 3], '-', linewidth=2, label='W3')
ax.plot(epochs_array, weights[:, 4], '-', linewidth=2, label='W4')
ax.legend()
plt.title("Plot the evolution of each coefficient of W")

plt.show()