import os
import json
import logging
import stat
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class ApiKeysManager:
    """Gerencia API Keys com persistência criptografada."""
    
    def __init__(self, storage_path: str = "database/api_keys.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Gerar ou carregar chave de criptografia
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Carregar chaves salvas
        self.keys = self._load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Obtém ou cria uma chave de criptografia.
        
        SEGURANÇA:
        - Tenta carregar de variável de ambiente primeiro (mais seguro)
        - Se não existir, cria arquivo .encryption_key com permissões restritas
        - Em produção, recomenda-se usar ENCRYPTION_KEY env var
        """
        # Prioridade 1: Variável de ambiente (MAIS SEGURO)
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            logger.info("🔐 Usando chave de criptografia de variável de ambiente (SEGURO)")
            return env_key.encode()
        
        # Prioridade 2: Arquivo local
        key_file = self.storage_path.parent / ".encryption_key"
        
        if key_file.exists():
            logger.info("🔐 Carregando chave de criptografia do arquivo")
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Gerar nova chave
            logger.warning("⚠️  Gerando nova chave de criptografia local")
            logger.warning("⚠️  Para produção, use ENCRYPTION_KEY env var!")
            
            key = Fernet.generate_key()
            
            # Salvar com permissões restritas (Unix-like)
            with open(key_file, "wb") as f:
                f.write(key)
            
            # Definir permissões: apenas owner pode ler/escrever (600)
            try:
                os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
                logger.info("✅ Permissões de arquivo definidas: 600 (somente owner)")
            except (OSError, AttributeError):
                # Windows não suporta chmod da mesma forma
                logger.warning("⚠️  Não foi possível definir permissões Unix (provavelmente Windows)")
            
            logger.info("✅ Nova chave de criptografia gerada e salva")
            return key
    
    def _encrypt(self, text: str) -> str:
        """Criptografa um texto."""
        if not text:
            return ""
        return self.cipher.encrypt(text.encode()).decode()
    
    def _decrypt(self, encrypted_text: str) -> str:
        """Descriptografa um texto."""
        if not encrypted_text:
            return ""
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logger.error(f"Erro ao descriptografar: {e}")
            return ""
    
    def _load_keys(self) -> Dict[str, str]:
        """
        Carrega chaves do arquivo.
        
        SEGURANÇA:
        - Verifica integridade do arquivo
        - Suporta formato antigo e novo (backward compatibility)
        """
        if not self.storage_path.exists():
            logger.info("📁 Nenhum arquivo de chaves encontrado (primeira execução)")
            return {}
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            # Suportar formato novo (com metadata)
            if isinstance(data, dict) and "keys" in data:
                encrypted_data = data["keys"]
                logger.info(f"📁 Carregando formato v{data.get('version', '1.0')}")
            else:
                # Formato antigo (backward compatibility)
                encrypted_data = data
            
            # Descriptografar
            keys = {}
            for key, encrypted_value in encrypted_data.items():
                decrypted = self._decrypt(encrypted_value)
                if decrypted:  # Só adicionar se descriptografou com sucesso
                    keys[key] = decrypted
            
            logger.info(f"✅ Chaves carregadas: {list(keys.keys())}")
            return keys
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Arquivo de chaves corrompido: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Erro ao carregar chaves: {e}")
            return {}
    
    def _save_keys(self):
        """
        Salva chaves no arquivo com criptografia.
        
        SEGURANÇA:
        - Criptografa antes de salvar
        - Define permissões restritas no arquivo (Unix)
        - Adiciona metadata de quando foi salvo
        """
        try:
            # Criptografar
            encrypted_data = {}
            for key, value in self.keys.items():
                if value:  # Só salvar se tiver valor
                    encrypted_data[key] = self._encrypt(value)
            
            # Adicionar metadata (não sensível)
            data_to_save = {
                "version": "1.0",
                "encrypted": True,
                "keys": encrypted_data
            }
            
            # Salvar
            with open(self.storage_path, "w") as f:
                json.dump(data_to_save, f, indent=2)
            
            # Definir permissões: apenas owner pode ler/escrever (600)
            try:
                os.chmod(self.storage_path, stat.S_IRUSR | stat.S_IWUSR)
            except (OSError, AttributeError):
                pass  # Windows não suporta chmod da mesma forma
            
            logger.info(f"✅ Chaves salvas criptografadas: {list(encrypted_data.keys())}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao salvar chaves: {e}")
    
    def get(self, key: str) -> Optional[str]:
        """Obtém uma chave."""
        return self.keys.get(key)
    
    def set(self, key: str, value: str):
        """Define uma chave."""
        self.keys[key] = value
        self._save_keys()
    
    def set_multiple(self, keys_dict: Dict[str, str]):
        """Define múltiplas chaves de uma vez."""
        self.keys.update(keys_dict)
        self._save_keys()
    
    def delete(self, key: str):
        """Remove uma chave."""
        if key in self.keys:
            del self.keys[key]
            self._save_keys()
    
    def get_all(self) -> Dict[str, str]:
        """Retorna todas as chaves."""
        return self.keys.copy()
    
    def has_key(self, key: str) -> bool:
        """Verifica se uma chave existe e não está vazia."""
        return bool(self.keys.get(key))


# Instância global
api_keys_manager = ApiKeysManager()
