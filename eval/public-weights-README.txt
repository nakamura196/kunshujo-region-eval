best.pt (git には入れない。commit しない)
  取得元: https://huggingface.co/spaces/nakamura196/yolov5-kunshujo/resolve/main/best.pt
  取得日時: 2026-10-16 21:29 (JST ごろ)
  サイズ: 699148621 bytes
  sha256: afb897f715523f8a2a49b542124e667240f77f8c69a41fb789bd161060a63165
  備考: YOLOv5 (yolov5x 相当, 87,198,694 パラメータ, 1 クラス)。dev も test も含む全データで学習された重み。

best.onnx (git には入れない。commit しない)
  作り方: ultralytics/yolov5 tag v7.0 の export.py --include onnx --imgsz 640 --opset 12 (torch 2.8.0 / onnx 1.19.1)
          torch.load の weights_only=False パッチ付き。--simplify は onnxsim がこの環境(Python 3.9)で入らず未使用。
  入力: 1x3x640x640 (固定), 出力: 1x25200x6 (NMS は含まない)。640 は app.py の実効推論サイズ。
  サイズ: 349298521 bytes
  sha256: f80a4842ea6bb64be32c1b1ca193fea30ac3a01a4ffaeef6d27768b39f3c0732
  検証: dev 20 コマで PyTorch と onnxruntime(CPU) を同じ入力で比較 → 枠 167/167 対応、IoU 最小 1.0000、確信度差の最大 0.00000 (小数 5 桁)
