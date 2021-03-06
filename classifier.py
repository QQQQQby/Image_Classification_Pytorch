# coding: utf-8
import random
import sys
import time

import torch
from torch import nn, optim
import numpy as np
import argparse
import os
from tqdm import tqdm

import data_loaders
import metrics
import modules


class Classifier:
    def __init__(self, args):
        print(args)
        self.args = args

        self.model = modules.CNN1()

        print('-' * 20 + 'Reading data' + '-' * 20, flush=True)
        data_loader = data_loaders.TF2DataLoader(args.dataset_path)
        self.data_train = data_loader.get_data_train()
        self.data_dev = data_loader.get_data_dev()
        self.data_test = data_loader.get_data_test()
        self.labels = data_loader.get_labels()

    def run(self):
        if not os.path.exists(self.args.output_path):
            os.makedirs(self.args.output_path)
        for epoch in range(self.args.epochs):
            if not self.args.not_train:
                """Train"""
                print('-' * 20 + 'Training epoch %d' % epoch + '-' * 20, flush=True)
                time.sleep(0.1)
                m = metrics.Metrics(self.labels)
                random.shuffle(self.data_train)
                optimizer = optim.SGD(self.model.parameters(), lr=self.args.lr)
                for start in tqdm(range(0, len(self.data_train), self.args.train_batch_size),
                                  desc='Training batch: '):
                    images = [d[0] for d in self.data_train[start:start + self.args.train_batch_size]]
                    actual_labels = [d[1] for d in self.data_train[start:start + self.args.train_batch_size]]
                    """forward"""
                    batch_images = torch.tensor(images, dtype=torch.float32)
                    outputs = self.model(batch_images)
                    """backward"""
                    batch_labels = torch.tensor(actual_labels, dtype=torch.int64)
                    self.model.zero_grad()
                    loss = nn.CrossEntropyLoss()(outputs, batch_labels)
                    loss.backward()
                    optimizer.step()
                    """update confusion matrix"""
                    pred_labels = outputs.softmax(1).argmax(1).tolist()
                    m.update(actual_labels, pred_labels)
                print(m.get_accuracy())
                if self.args.save:
                    self.save(epoch)

            if not self.args.not_eval:
                """Eval"""
                print('-' * 20 + 'Evaluating epoch %d' % epoch + '-' * 20, flush=True)
                time.sleep(0.1)
                m = metrics.Metrics(self.labels)
                for start in tqdm(range(0, len(self.data_dev), self.args.dev_batch_size),
                                  desc='Evaluating batch: '):
                    images = [d[0] for d in self.data_dev[start:start + self.args.dev_batch_size]]
                    actual_labels = [d[1] for d in self.data_dev[start:start + self.args.dev_batch_size]]
                    """forward"""
                    batch_images = torch.tensor(images, dtype=torch.float32)
                    outputs = self.model(batch_images)
                    """update confusion matrix"""
                    pred_labels = outputs.softmax(1).argmax(1).tolist()
                    m.update(actual_labels, pred_labels)
                """evaluate"""
                print(m.get_accuracy())

            if not self.args.not_test:
                """Test"""
                print('-' * 20 + 'Testing epoch %d' % epoch + '-' * 20, flush=True)
                time.sleep(0.1)
                m = metrics.Metrics(self.labels)
                for start in tqdm(range(0, len(self.data_test), self.args.test_batch_size),
                                  desc='Testing batch: '):
                    images = [d[0] for d in self.data_test[start:start + self.args.test_batch_size]]
                    actual_labels = [d[1] for d in self.data_test[start:start + self.args.test_batch_size]]
                    """forward"""
                    batch_images = torch.tensor(images, dtype=torch.float32)
                    outputs = self.model(batch_images)
                    """update confusion matrix"""
                    pred_labels = outputs.softmax(1).argmax(1).tolist()
                    m.update(actual_labels, pred_labels)
                """testing"""
                print(m.get_accuracy())
            print()

    def save(self, epoch):
        path = os.path.join(self.args.output_path, 'epoch_' + str(epoch) + '.pd')
        torch.save(self.model, path)


def parse_args():
    parser = argparse.ArgumentParser(description="Run MNIST Classifier.")
    parser.add_argument('--dataset_path', type=str, default='./data',
                        help='Dataset path.')
    parser.add_argument('--output_path', type=str, default='./output/1000_0.01_dropout0.7',
                        help='Output path.')

    parser.add_argument('--not_train', action='store_true', default=False,
                        help="Whether not to train the model.")
    parser.add_argument('--save', action='store_true', default=False,
                        help="Whether to save the model after training.")
    parser.add_argument('--train_batch_size', type=int, default=1000,
                        help='Batch size of train set.')
    parser.add_argument('--epochs', type=int, default=20,
                        help='Number of epochs.')
    parser.add_argument('--lr', type=float, default=0.01,
                        help='Learning rate.')

    parser.add_argument('--not_eval', action='store_true', default=False,
                        help="Whether not to evaluate the model.")
    parser.add_argument('--dev_batch_size', type=int, default=2000,
                        help='Batch size of dev set.')

    parser.add_argument('--not_test', action='store_true', default=False,
                        help="Whether not to test the model.")
    parser.add_argument('--test_batch_size', type=int, default=2000,
                        help='Batch size of test set.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    if torch.cuda.is_available():
        torch.set_default_tensor_type('torch.cuda.FloatTensor')
    classifier = Classifier(args)
    classifier.run()
