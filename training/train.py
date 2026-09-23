import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, accuracy_score

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, SpatialDropout1D, Bidirectional, LSTM, Dense, Dropout, GlobalMaxPooling1D, Conv1D
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2

def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def augment_text(text):
    words = text.split()
    augmented = [text]
    if len(words) > 3:
        # Drop one random word
        augmented.append(" ".join(words[1:]))
        augmented.append(" ".join(words[:-1]))
        augmented.append(" ".join([words[0]] + words[2:]))
    return augmented

def main():
    print("=== VocaSense Universal Open Model Training Pipeline ===")
    
    # Paths setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "intents.json")
    model_dir = os.path.join(base_dir, "model")
    static_assets_dir = os.path.join(base_dir, "static_assets")
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(static_assets_dir, exist_ok=True)
    
    # 1. Load Data
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    raw_patterns = []
    raw_labels = []
    metadata_dict = {}

    for intent in data["intents"]:
        tag = intent["tag"]
        metadata_dict[tag] = {
            "category": intent.get("category", "General"),
            "responses": intent.get("responses", []),
            "suggested_action": intent.get("suggested_action", "Explore available topics."),
            "entity": intent.get("entity", "general")
        }
        for pattern in intent["patterns"]:
            cleaned = clean_text(pattern)
            if cleaned:
                for aug in augment_text(cleaned):
                    raw_patterns.append(aug)
                    raw_labels.append(tag)
                
    print(f"[DATA] Total augmented samples: {len(raw_patterns)}")
    print(f"[DATA] Total intent categories: {len(metadata_dict)}")
    
    # 2. Tokenization & Sequence Padding
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(raw_patterns)
    vocab_size = len(tokenizer.word_index) + 1
    
    sequences = tokenizer.texts_to_sequences(raw_patterns)
    max_len = max(len(s) for s in sequences)
    max_len = max(max_len, 15)
    
    X = pad_sequences(sequences, maxlen=max_len, padding="post", truncating="post")
    
    # 3. Label Encoding
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(raw_labels)
    num_classes = len(label_encoder.classes_)
    
    # 4. Stratified Split (80% Train, 10% Val, 10% Test)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y_encoded, test_size=0.15, random_state=42, stratify=y_encoded
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val
    )
    
    print(f"[SPLIT] Training samples: {len(X_train)}")
    print(f"[SPLIT] Validation samples: {len(X_val)}")
    print(f"[SPLIT] Test samples: {len(X_test)}")
    
    # Save split info
    split_info = {
        "total_samples": len(X),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "vocab_size": vocab_size,
        "max_len": max_len,
        "num_classes": num_classes,
        "classes": list(label_encoder.classes_)
    }
    with open(os.path.join(base_dir, "data", "train_test_split.json"), "w", encoding="utf-8") as f:
        json.dump(split_info, f, indent=2)
        
    # 5. Robust Neural Architecture: Embedding -> SpatialDropout -> Conv1D -> BiLSTM -> GlobalMaxPooling -> Dense -> Softmax
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=64, input_length=max_len),
        SpatialDropout1D(0.2),
        Conv1D(filters=64, kernel_size=3, padding="same", activation="relu"),
        Bidirectional(LSTM(64, return_sequences=True)),
        GlobalMaxPooling1D(),
        Dense(64, activation="relu", kernel_regularizer=l2(0.001)),
        Dropout(0.3),
        Dense(num_classes, activation="softmax")
    ])
    
    optimizer = Adam(learning_rate=0.003)
    model.compile(
        optimizer=optimizer,
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    model.summary()
    
    # 6. Train with Callbacks
    early_stop = EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=0.0001, verbose=1)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=40,
        batch_size=16,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    # 7. Save Model & Artifacts
    model_path = os.path.join(model_dir, "intent_model.keras")
    model.save(model_path)
    print(f"[SAVED] Keras Model -> {model_path}")
    
    tokenizer_json = tokenizer.to_json()
    with open(os.path.join(model_dir, "tokenizer.json"), "w", encoding="utf-8") as f:
        f.write(tokenizer_json)
        
    encoder_data = {
        "classes": list(label_encoder.classes_),
        "max_len": max_len
    }
    with open(os.path.join(model_dir, "label_encoder.json"), "w", encoding="utf-8") as f:
        json.dump(encoder_data, f, indent=2)
        
    with open(os.path.join(model_dir, "intent_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata_dict, f, indent=2)

    # 8. Evaluate on Test Set
    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    acc = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    
    print("\n" + "="*50)
    print("=== TEST SET EVALUATION METRICS ===")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall   : {recall * 100:.2f}%")
    print(f"F1-Score : {f1 * 100:.2f}%")
    print("="*50)
    
    class_names = list(label_encoder.classes_)
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))
    
    # Save evaluation metrics json
    eval_metrics = {
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "total_parameters": int(model.count_params()),
        "epochs_trained": len(history.history["loss"])
    }
    with open(os.path.join(model_dir, "evaluation_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(eval_metrics, f, indent=2)

    # 9. Save Loss / Accuracy Plots
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history["accuracy"], label="Train Accuracy", color="#00ffa3", linewidth=2)
    plt.plot(history.history["val_accuracy"], label="Val Accuracy", color="#3b82f6", linewidth=2, linestyle="--")
    plt.title("VocaSense Universal Model - Accuracy Curve", fontsize=12, fontweight="bold")
    plt.xlabel("Epochs")
    plt.ylabel("Accuracy")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history["loss"], label="Train Loss", color="#ef4444", linewidth=2)
    plt.plot(history.history["val_loss"], label="Val Loss", color="#f59e0b", linewidth=2, linestyle="--")
    plt.title("VocaSense Universal Model - Loss Curve", fontsize=12, fontweight="bold")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plot_path = os.path.join(static_assets_dir, "loss_accuracy_plot.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"[PLOT] Loss/Accuracy Curves saved -> {plot_path}")
    
    # 10. Save Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=class_names, yticklabels=class_names,
                cbar=True, square=True)
    plt.title("VocaSense Universal Intent Classifier - Confusion Matrix", fontsize=13, fontweight="bold", pad=15)
    plt.xlabel("Predicted Intent Tag", fontsize=10, fontweight="bold")
    plt.ylabel("True Intent Tag", fontsize=10, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    
    cm_path = os.path.join(static_assets_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[PLOT] Confusion Matrix saved -> {cm_path}")
    print("\n=== Training & Evaluation Complete Successfully! ===")

if __name__ == "__main__":
    main()
