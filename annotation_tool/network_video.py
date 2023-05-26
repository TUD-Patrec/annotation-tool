"""
@created: 24.10.2022
@author: Fernando Moya Rueda

@brief: Modus Selecter for video HAR
"""
from __future__ import print_function

import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet18_Weights


class Network(nn.Module):
    def __init__(self, config):
        super(Network, self).__init__()
        self.config = config

        rnn_hidden_size = 128
        rnn_num_layers = 1

        # baseModel = models.resnet18(pretrained=True)
        baseModel = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        num_features = baseModel.fc.in_features
        baseModel.fc = Identity()
        self.baseModel = baseModel
        self.dropout = nn.Dropout(0.1)
        self.rnn = nn.LSTM(num_features, rnn_hidden_size, rnn_num_layers)
        self.fc1 = nn.Linear(rnn_hidden_size, 64)
        self.fc2 = nn.Linear(64, self.config["num_classes"])

    def forward(self, x):
        b_z, ts, c, h, w = x.shape
        ii = 0
        y = self.baseModel((x[:, ii]))
        output, (hn, cn) = self.rnn(y.unsqueeze(1))
        for ii in range(1, ts):
            y = self.baseModel((x[:, ii]))
            out, (hn, cn) = self.rnn(y.unsqueeze(1), (hn, cn))
        out = self.dropout(out[:, -1])
        out = self.fc1(out)
        out = self.fc2(out)
        return out


class Identity(nn.Module):
    def __init__(self):
        super(Identity, self).__init__()

    def forward(self, x):
        return x


if __name__ == "__main__":
    import time

    from media_reader import media_reader
    import torch
    from torch.nn import Softmax
    from torchvision import transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model_path = r"C:\Users\Raphael\Desktop\video_network.pt"
    video_path = r"C:\Users\Raphael\Desktop\Brownie.avi"

    state = torch.load(model_path, map_location=torch.device("cpu"))
    print(state.keys())
    print(state["att_rep"]["Sandwich"].astype(int).shape)
    model = Network(state["network_config"])
    model.load_state_dict(state["state_dict"])

    model.to(device)

    video = media_reader(video_path)

    predictions = []

    lo = 0
    fps = 30
    window_size = 30
    batch_size = 30

    acc_1 = 0
    acc_2 = 0
    acc_3 = 0

    stop_after = 30

    h, w = 112, 112
    mean = [0.43216, 0.394666, 0.37645]
    std = [0.22803, 0.22145, 0.216989]

    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Resize((h, w), antialias=True),
            transforms.Normalize(mean, std),
        ]
    )

    with torch.no_grad():
        while lo + window_size < len(video):
            start_1 = time.perf_counter()
            print(f"Progress: {lo / len(video) :.2f}")

            batch = []

            for idx in range(batch_size):
                if lo + window_size > len(video):
                    break
                start_3 = time.perf_counter()
                window = list(video[lo : lo + window_size])
                end_3 = time.perf_counter()
                acc_3 += end_3 - start_3
                window = [transform(x) for x in window]
                window = torch.stack(window, dim=0)

                if len(window.shape) == 2:
                    window = window.unsqueeze(0)  # add time dimension

                window = window.unsqueeze(0)  # add batch dimension
                batch.append(window)
                lo += window_size

            assert len(batch) > 0

            batch = torch.cat(batch, dim=0)
            assert (
                len(batch.shape) == 5
            ), f"{batch.shape =} but should be (batch, time, channels, height, width)"

            x = batch.to(device)

            start_2 = time.perf_counter()
            Y = model(x)
            Y = Softmax(dim=1)(Y)
            end_2 = time.perf_counter()

            predictions.extend(Y.cpu().numpy().tolist())
            print(f"{len(predictions) = }")

            end_1 = time.perf_counter()

            acc_1 += end_1 - start_1
            acc_2 += end_2 - start_2

            print(f"{acc_2 / acc_1 = }")
            print(f"{acc_3 / acc_1 = }")

            print(f"Time spend: {acc_1} s")
            if acc_1 > stop_after:
                print("Stopping early")
                progress = lo / len(video)
                print(f"Progress: {progress}")

                expected_time = acc_1 / progress
                print(f"Expected time when using {device}: {expected_time}")

                break

    print(f"Prediction-time: {acc_2}")
    print(f"Total-time: {acc_1}")
    print(f"Relative prediction-time: {acc_2 / acc_1}")
    print(f"Relative video_reading-time: {acc_3 / acc_1}")
    print(*predictions[:10], sep="\n")
