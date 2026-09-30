import numpy as np
from datasketch import MinHash, MinHashLSH
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, threshold=0.2):
        self.lsh = MinHashLSH(threshold=threshold, num_perm=128)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.minhashes = {}
        self.records = {}
        
    def _get_minhash(self, text: str) -> MinHash:
        tokens = text.split()
        m = MinHash(num_perm=128)
        for token in tokens:
            m.update(token.encode('utf8'))
        return m

    def build_index(self, records: List[Dict]):
        logger.info("Building LSH index and computing embeddings...")
        
        texts = []
        ids = []
        for r in records:
            id_ = r['internal_id']
            text = r['cleaned_description']
            self.records[id_] = r
            
            mh = self._get_minhash(text)
            self.minhashes[id_] = mh
            self.lsh.insert(id_, mh)
            
            texts.append(text)
            ids.append(id_)
            
        logger.info("Computing embeddings...")
        embeddings = self.model.encode(texts)
        self.embeddings = {id_: emb for id_, emb in zip(ids, embeddings)}
        logger.info("Index built.")

    def _attribute_score(self, attr1: Dict, attr2: Dict) -> float:
        score = 0.0
        
        if 'material_type' in attr1 and 'material_type' in attr2:
            if attr1['material_type'] == attr2['material_type']:
                score += 0.3
                
        if 'dimensions' in attr1 and 'dimensions' in attr2:
            if set(attr1['dimensions']) & set(attr2['dimensions']):
                score += 0.2
                
        if 'standard' in attr1 and 'standard' in attr2:
            if attr1['standard'] == attr2['standard']:
                score += 0.2
                
        if 'connector_type' in attr1 and 'connector_type' in attr2:
            if attr1['connector_type'] == attr2['connector_type']:
                score += 0.15
                
        if 'pin_count' in attr1 and 'pin_count' in attr2:
            if attr1['pin_count'] == attr2['pin_count']:
                score += 0.15
                
        return min(1.0, score)

    def find_matches(self, record_id: str) -> List[Dict]:
        if record_id not in self.records:
            return []
            
        target_mh = self.minhashes[record_id]
        target_emb = self.embeddings[record_id].reshape(1, -1)
        target_attr = self.records[record_id].get('attributes', {})
        
        candidates = self.lsh.query(target_mh)
        
        matches = []
        for cand_id in candidates:
            if cand_id == record_id:
                continue
                
            cand_emb = self.embeddings[cand_id].reshape(1, -1)
            cand_attr = self.records[cand_id].get('attributes', {})
            
            sem_score = cosine_similarity(target_emb, cand_emb)[0][0]
            attr_score = self._attribute_score(target_attr, cand_attr)
            
            combined_score = 0.6 * sem_score + 0.4 * attr_score
            
            if combined_score >= 0.75:
                match_type = "IDENTICAL"
            elif combined_score >= 0.55:
                match_type = "EQUIVALENT"
            elif combined_score >= 0.40:
                match_type = "SIMILAR"
            else:
                match_type = "DIFFERENT"
                
            if combined_score >= 0.40:
                matches.append({
                    'source_id': record_id,
                    'target_id': cand_id,
                    'semantic_score': float(sem_score),
                    'attribute_score': float(attr_score),
                    'combined_score': float(combined_score),
                    'match_type': match_type
                })
                
        return sorted(matches, key=lambda x: x['combined_score'], reverse=True)

    def run_all_matches(self) -> List[Dict]:
        logger.info("Running all matches...")
        all_matches = []
        processed = set()
        for i, r_id in enumerate(self.records.keys()):
            if i % 100 == 0:
                logger.info(f"Processed {i} records for matching")
            matches = self.find_matches(r_id)
            for m in matches:
                pair = tuple(sorted([m['source_id'], m['target_id']]))
                if pair not in processed:
                    all_matches.append(m)
                    processed.add(pair)
        return all_matches
