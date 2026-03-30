import os

import jieba
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import DATA_DIR

jieba.initialize()


class QARetrievalSystem:
    def __init__(self, qa_dir=None):
        if qa_dir is None:
            self.qa_dir = str(DATA_DIR)
        else:
            self.qa_dir = os.path.join(str(DATA_DIR), qa_dir)
        print(f"QA目录路径: {self.qa_dir}")
        self.qa_pairs = []
        self.questions = []
        self.vectorizer = TfidfVectorizer(tokenizer=self._tokenize)

    @staticmethod
    def _tokenize(text):
        return [t for t in jieba.cut(text) if t.strip()]

    def load_qa_pairs(self):
        if not os.path.exists(self.qa_dir):
            print(f"QA目录 {self.qa_dir} 不存在")
            return False
        for name in os.listdir(self.qa_dir):
            if name.endswith(".xlsx"):
                self._load_xlsx(os.path.join(self.qa_dir, name))
        if not self.qa_pairs:
            print("未加载到任何QA对")
            return False
        self.questions = [qa["question"] for qa in self.qa_pairs]
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)
        return True

    def _load_xlsx(self, file_path):
        try:
            xls = pd.ExcelFile(file_path)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                q_col = a_col = None
                for col in df.columns:
                    low = col.lower()
                    if any(k in low for k in ("question", "query")) or "问题" in col:
                        q_col = col
                    if "answer" in low or "答案" in col:
                        a_col = col
                if q_col and a_col:
                    for _, row in df.iterrows():
                        q = str(row[q_col]).strip()
                        a = str(row[a_col]).strip()
                        if q:
                            self.qa_pairs.append({
                                "question": q,
                                "answer": a,
                                "source": f"{file_path}[{sheet}]",
                            })
                else:
                    print(f"xlsx {file_path} 工作表 {sheet} 中未找到问题/答案列")
        except Exception as e:
            print(f"加载 {file_path} 出错: {e}")

    def search(self, user_question, top_n=5, threshold=0.1):
        if not self.questions:
            return []
        user_vec = self.vectorizer.transform([user_question])
        sims = cosine_similarity(user_vec, self.tfidf_matrix)[0]
        top_idx = np.argsort(sims)[::-1][:top_n]
        return [
            {
                "question": self.qa_pairs[i]["question"],
                "answer": self.qa_pairs[i]["answer"],
                "similarity": sims[i],
                "source": self.qa_pairs[i]["source"],
            }
            for i in top_idx
            if sims[i] >= threshold
        ]


@st.cache_resource
def get_retrieval_system():
    """全局单例，仅在首次调用时加载 xlsx + 构建 TF-IDF 索引"""
    system = QARetrievalSystem()
    system.load_qa_pairs()
    return system
