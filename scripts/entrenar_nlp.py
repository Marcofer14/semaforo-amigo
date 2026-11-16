"""Entrena los 4 clasificadores y guarda métricas.  Uso:  python -m scripts.entrenar_nlp"""
import json

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from src.config import DATASET, METRICAS, MODELO_NLP, MODELOS
from src.nlp import ETIQUETAS, ORDEN, gravedad_por_reglas


def nuevo_modelo():
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, strip_accents="unicode", lowercase=True),
        LogisticRegression(C=10, max_iter=2000, class_weight="balanced"),
    )


def main():
    df = pd.read_csv(DATASET, sep=";")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    metricas, modelos = {"n_frases": len(df)}, {}
    for etiqueta in ETIQUETAS:
        # Validación cruzada: cada frase se predice con un modelo que no la vio.
        pred = cross_val_predict(nuevo_modelo(), df["texto"], df[etiqueta], cv=cv)
        metricas[etiqueta] = {
            "accuracy": round(accuracy_score(df[etiqueta], pred), 3),
            "f1_macro": round(f1_score(df[etiqueta], pred, average="macro"), 3),
            "clases": df[etiqueta].value_counts().to_dict(),
        }
        print(f"\n=== {etiqueta} ===\n{classification_report(df[etiqueta], pred, zero_division=0)}")
        if etiqueta == "gravedad":
            final = [max(p, gravedad_por_reglas(t), key=ORDEN.get) for p, t in zip(pred, df["texto"])]
            rojo = df["gravedad"] == "rojo"
            metricas["gravedad_modelo_mas_reglas"] = {
                "accuracy": round(accuracy_score(df["gravedad"], final), 3),
                "f1_macro": round(f1_score(df["gravedad"], final, average="macro"), 3),
                "recall_rojo_solo_modelo": round(float((pred[rojo] == "rojo").mean()), 3),
                "recall_rojo_con_reglas": round(float((pd.Series(final)[rojo.values] == "rojo").mean()), 3),
            }
        modelos[etiqueta] = nuevo_modelo().fit(df["texto"], df[etiqueta])

    MODELOS.mkdir(exist_ok=True)
    METRICAS.mkdir(exist_ok=True)
    joblib.dump(modelos, MODELO_NLP)
    (METRICAS / "nlp.json").write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in metricas.items() if k != "n_frases"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
