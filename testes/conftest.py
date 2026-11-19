"""Torna importáveis os módulos dos projetos (sem instalar nada)."""
import os, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'projetos', 'artigo2_caixacinza', 'codigo'))
sys.path.insert(0, os.path.join(RAIZ, 'projetos', 'artigo1_coorte'))
os.environ.setdefault('NTHREADS', '1')
