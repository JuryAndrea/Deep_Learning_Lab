# -*- coding: utf-8 -*-
"""Assignment3_helper_code_2022_Jury_Andrea_D'Onofrio.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pEEgjE5cIFPuS4mI-PTiIV2VXXa7CBb9

# Helper Code for Assignment 3 (RNN language models)

## Reading raw text file & Create DataLoader
"""

import os

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from tqdm.notebook import tqdm, trange

class Vocabulary:

    def __init__(self, pad_token="<pad>", unk_token='<unk>'):
        self.id_to_string = {}
        self.string_to_id = {}
        
        # add the default pad token
        self.id_to_string[0] = pad_token
        self.string_to_id[pad_token] = 0
        
        # add the default unknown token
        self.id_to_string[1] = unk_token
        self.string_to_id[unk_token] = 1        
        
        # shortcut access
        self.pad_id = 0
        self.unk_id = 1
        
    def __len__(self):
        return len(self.id_to_string)

    def add_new_word(self, string):
        self.string_to_id[string] = len(self.string_to_id)
        self.id_to_string[len(self.id_to_string)] = string

    # Given a string, return ID
    def get_idx(self, string, extend_vocab=False):
        if string in self.string_to_id:
            return self.string_to_id[string]
        elif extend_vocab:  # add the new word
            self.add_new_word(string)
            return self.string_to_id[string]
        else:
            return self.unk_id


# Read the raw txt file and generate a 1D PyTorch tensor
# containing the whole text mapped to sequence of token IDs, and a vocab object.
class TextData:

    def __init__(self, file_path, vocab=None, extend_vocab=True, device='cuda'):
        self.data, self.vocab = self.text_to_data(file_path, vocab, extend_vocab, device)
        
    def __len__(self):
        return len(self.data)

    def text_to_data(self, text_file, vocab, extend_vocab, device):
        """Read a raw text file and create its tensor and the vocab.

        Args:
          text_file: a path to a raw text file.
          vocab: a Vocab object
          extend_vocab: bool, if True extend the vocab
          device: device

        Returns:
          Tensor representing the input text, vocab file

        """
        assert os.path.exists(text_file)
        if vocab is None:
            vocab = Vocabulary()

        data_list = []

        # Construct data
        full_text = []
        print(f"Reading text file from: {text_file}")
        with open(text_file, 'r') as text:
            for line in text:
                tokens = list(line)
                for token in tokens:
                    # get index will extend the vocab if the input
                    # token is not yet part of the text.
                    full_text.append(vocab.get_idx(token, extend_vocab=extend_vocab))

        # convert to tensor
        data = torch.tensor(full_text, device=device, dtype=torch.int64)
        print("Done.")

        return data, vocab
    

# Since there is no need for schuffling the data, we just have to split
# the text data according to the batch size and bptt length.
# The input to be fed to the model will be batch[:-1]
# The target to be used for the loss will be batch[1:]
class DataBatches:

    def __init__(self, data, bsz, bptt_len, pad_id):
        self.batches = self.create_batch(data, bsz, bptt_len, pad_id)

    def __len__(self):
        return len(self.batches)

    def __getitem__(self, idx):
        return self.batches[idx]

    def create_batch(self, input_data, bsz, bptt_len, pad_id):
        """Create batches from a TextData object .

        Args:
          input_data: a TextData object.
          bsz: int, batch size
          bptt_len: int, bptt length
          pad_id: int, ID of the padding token

        Returns:
          List of tensors representing batches

        """
        batches = []  # each element in `batches` is (len, B) tensor
        text_len = len(input_data)
        segment_len = text_len // bsz + 1

        # Question: Explain the next two lines!
        # print(f"pad_id {pad_id}")
        
        padded = input_data.data.new_full((segment_len * bsz,), pad_id)
        
        # print(f"segment_len * bsz = {segment_len * bsz}")

        # print(input_data.data.new_full((segment_len * bsz,), pad_id))

        # print(f"padded {padded}")
        # print(f"padded shape {padded.shape}")
        
        padded[:text_len] = input_data.data
        
        # print(f" text len {text_len}")
        # print(f"padded {padded}")
        # print(f"input_data {input_data}")
        # print(f"input_data.data {input_data.data}")
        # .new_full Returns a Tensor of size (segment_len * bsz,) filled with pad_id. 



        padded = padded.view(bsz, segment_len).t()
        num_batches = segment_len // bptt_len + 1

        for i in range(num_batches):
            # Prepare batches such that the last symbol of the current batch
            # is the first symbol of the next batch.
            if i == 0:
                # Append a dummy start symbol using pad token
                batch = torch.cat(
                    [padded.new_full((1, bsz), pad_id),
                     padded[i * bptt_len:(i + 1) * bptt_len]], dim=0)
                batches.append(batch)
                # print(f"bsz {bsz}")
                # print(f"bptt_len {bptt_len}")
                # print(f"padded[i * bptt len:(i + 1) * bptt len] {padded[i * bptt_len:(i + 1) * bptt_len].shape}")
            else:
                batches.append(padded[i * bptt_len - 1:(i + 1) * bptt_len])
                # print(f"bsz {bsz}")
                # print(f"bptt_len {bptt_len}")
                # print(f"padded[i * bptt_len - 1:(i + 1) * bptt_len] {padded[i * bptt_len - 1:(i + 1) * bptt_len].shape}")

        return batches

# downlaod the text
# Make sure to go to the link and check how the text looks like.
!wget http://www.gutenberg.org/files/49010/49010-0.txt

# This is for Colab. Adapt the path if needed.
text_path = "/content/49010-0.txt"
# text_path = "/content/dll2.txt"

DEVICE = 'cuda'

batch_size = 32
bptt_len = 64

my_data = TextData(text_path, device=DEVICE)
batches = DataBatches(my_data, batch_size, bptt_len, pad_id=0)

"""## Model"""

# RNN based language model
class RNNModel(nn.Module):

    def __init__(self, num_classes, emb_dim, hidden_dim, num_layers):
        """Parameters:
        
          num_classes (int): number of input/output classes
          emb_dim (int): token embedding size
          hidden_dim (int): hidden layer size of RNNs
          num_layers (int): number of RNN layers
        """
        super().__init__()
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.input_layer = nn.Embedding(num_classes, emb_dim)
        self.rnn = nn.RNN(emb_dim, hidden_dim, num_layers)
        self.out_layer = nn.Linear(hidden_dim, num_classes)

    def forward(self, input, state):
        emb = self.input_layer(input)
        output, state = self.rnn(emb, state)
        
        output = self.out_layer(output)
        output = output.view(-1, self.num_classes)
        return output, state

    def init_hidden(self, bsz):
        weight = next(self.parameters())
        return weight.new_zeros(self.num_layers, bsz, self.hidden_dim)


# To be modified for LSTM...
def custom_detach(h):
    return h.detach()

# LSTM based language model
class LSTMModel(nn.Module):

    def __init__(self, num_classes, emb_dim, hidden_dim, num_layers):
        """Parameters:
        
          num_classes (int): number of input/output classes
          emb_dim (int): token embedding size
          hidden_dim (int): hidden layer size of RNNs
          num_layers (int): number of RNN layers
        """
        super().__init__()
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.input_layer = nn.Embedding(num_classes, emb_dim)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers)
        self.out_layer = nn.Linear(hidden_dim, num_classes)

    def forward(self, input, state):
        emb = self.input_layer(input)
        output, state = self.lstm(emb, state)
        
        output_layer = self.out_layer(output)
        # print(f"1 {output_layer.shape}")
        # print(f"2 {state[0].shape}")
        # print(f"3 {state[1].shape}")

        output_layer_view = output_layer.view(-1, self.num_classes)
        # print(f"4 {output_layer_view.shape}")
        return output_layer_view, state

    def init_hidden(self, bsz):
      weight = next(self.parameters())
      return weight.new_zeros(self.num_layers, bsz, self.hidden_dim)

    def init_state(self, bsz):
      weight = next(self.parameters())
      return weight.new_zeros(self.num_layers, bsz, self.hidden_dim)


# To be modified for LSTM...
def custom_detach(h):
    return h.detach()

"""## Decoding"""

@torch.no_grad()
def complete(model, prompt, steps, sample=False):
    """Complete the prompt for as long as given steps using the model.
    
    Parameters:
      model: language model
      prompt (str): text segment to be completed
      steps (int): number of decoding steps.
      sample (bool): If True, sample from the model. Otherwise greedy.

    Returns:
      completed text (str)
    """
    model.eval()
    out_list = []
    
    # forward the prompt, compute prompt's ppl
    prompt_list = []
    char_prompt = list(prompt)
    for char in char_prompt:
        prompt_list.append(my_data.vocab.string_to_id[char])
    x = torch.tensor(prompt_list).to(DEVICE).unsqueeze(1)
    
    states = model.init_hidden(1).to(DEVICE)
    cell_state = model.init_state(1).to(DEVICE) #add for LSTM
    logits, states = model(x, (states, cell_state))
    probs = F.softmax(logits[-1], dim=-1)
        
    if sample:
      # assert False, "Implement me!"
      ix = torch.multinomial(probs, num_samples=1)
    else:
        max_p, ix = torch.topk(probs, k=1, dim=-1)

    out_list.append(my_data.vocab.id_to_string[int(ix)])
    x = ix.unsqueeze(1)
    
    # decode 
    for k in range(steps):
        logits, states = model(x, states)
        probs = F.softmax(logits, dim=-1)
        if sample:  # sample from the distribution or take the most likely
            # assert False, "Implement me!"
            ix = torch.multinomial(probs, num_samples=1)
        else:
            _, ix = torch.topk(probs, k=1, dim=-1)
        out_list.append(my_data.vocab.id_to_string[int(ix)])
        x = ix
    return ''.join(out_list)

# learning_rate = 0.0005
learning_rate = 0.001
clipping = 1.0
embedding_size = 64
rnn_size = 2048
rnn_num_layers = 1

# vocab_size = len(module.vocab.itos)
vocab_size = len(my_data.vocab.id_to_string)
print(F"vocab size: {vocab_size}")

# model = RNNModel(
#     num_classes=vocab_size, emb_dim=embedding_size, hidden_dim=rnn_size,
#     num_layers=rnn_num_layers)

model = LSTMModel(
    num_classes=vocab_size, emb_dim=embedding_size, hidden_dim=rnn_size,
    num_layers=rnn_num_layers)


model = model.to(DEVICE)
hidden = model.init_hidden(batch_size)

# print(hidden.shape)

loss_fn = nn.CrossEntropyLoss(ignore_index=0)
optimizer = torch.optim.Adam(params=model.parameters(), lr=learning_rate)



"""## Training loop"""

import numpy as np

# Training
num_epochs = 30
report_every = 30
prompt = "Dogs like best to"
# prompt = "train_set = torchvision.datasets.CIFAR10"

list_of_mean_ppl = []
beginning = ""
middle = ""
end = ""
best_perplexity = 1000
best_epoch = 0
best_batch = 0

model.to(DEVICE)

for ep in trange(num_epochs):
    print(f"=== start epoch {ep} ===")
    state = model.init_hidden(batch_size).to(DEVICE)
    cell_state = model.init_state(batch_size).to(DEVICE)
    list_of_ppl = []
    
    for idx in range(len(batches)):
        model.train()
        batch = batches[idx]    
        optimizer.zero_grad()
        state = custom_detach(state)
        cell_state = custom_detach(cell_state)
        
        input = batch[:-1]
        input = input.to(DEVICE)
        target = batch[1:].reshape(-1)

        bsz = input.shape[1]
        prev_bsz = state.shape[1]

        if bsz != prev_bsz:
            state = state[:, :bsz, :]
       
        # state = state, cell_state
        # print(input.shape)
        # print(state[0].shape)
        output, state = model(input, (state, cell_state))
        cell_state = state[1]
        state = state[0]
        # print(state)
        # print(state[0].shape)
        # print(state[1].shape)
        loss = loss_fn(output, target)
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), clipping)
        optimizer.step()
        perplexity  = torch.exp(loss)
        list_of_ppl.append(perplexity.item())

        if perplexity.item() < best_perplexity:
          best_perplexity = perplexity.item()
          best_epoch = ep
          best_batch = idx
        
        if idx % report_every == 0:
            # print(f"train loss: {loss.item()}")  # replace me by the line below!
            print(f"train ppl: {perplexity.item()}")
            generated_text = complete(model, prompt, 128, sample=False)
            print(f'----------------- epoch/batch {ep}/{idx} -----------------')
            print(prompt)
            print(generated_text)
            print(f'----------------- end generated text -------------------')
        
        if ep == 2 and idx == 0:
          beginning = generated_text
        if ep == 17 and idx == 30:
          middle = generated_text
        if ep == 28 and idx == 60:
          end = generated_text
    list_of_mean_ppl.append(np.mean(list_of_ppl))

print(best_perplexity)
print(best_epoch)
print(best_batch)

import matplotlib.pyplot as plt

print()

fig, ax = plt.subplots()
ax.plot(list_of_mean_ppl, linewidth=2, label='Training Perplexity')
ax.legend()
ax.set_xlabel("Epochs")
ax.set_ylabel("mean epoch's perplexity")
# plt.title("Training and validation losses over epochs")
plt.show()

print(f"{beginning}\n")
print(f"{middle}\n")
print(f"{end}")

input = "THE WOLF AND THE SHEEP"
print(complete(model, input, 512, sample=False))

input = "THE WOMAN AND HER MAN"
print(complete(model, input, 512, sample=False))

input = "IT WAS a sunny day"
print(complete(model, input, 512, sample=False))

input = "Home Alone"
print(complete(model, input, 512, sample=False))

input = "THE FOX AND THE GOAT"
print(complete(model, input, 512, sample=True))

input = "THE FOX AND THE GOAT"
print(complete(model, input, 512, sample=False))

input = "THE KING AND THE QUEEN"
print(complete(model, input, 512, sample=True))

input = "THE KING AND THE QUEEN"
print(complete(model, input, 512, sample=False))

input = "torchvision"
print(complete(model, input, 512, sample=False))

input = "CIFAR10"
print(complete(model, input, 512, sample=False))

input = "CrossEntropyLoss()"
print(complete(model, input, 512, sample=False))

input = "Evaluation"
print(complete(model, input, 512, sample=False))