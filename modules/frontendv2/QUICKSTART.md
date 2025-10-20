# ⚡ Início Rápido - Frontend v2

## 🚀 5 Passos para Começar

### 1️⃣ Instalar Dependências (2-3 minutos)

```powershell
cd d:\projetos\Transcricao-de-audio\modules\frontendv2
npm install
```

**Aguarde a instalação concluir...** ☕

### 2️⃣ Verificar Backend (30 segundos)

```powershell
# Testar se o backend está rodando
curl http://localhost:2020/health
```

**Resposta esperada:**
```json
{
  "status": "ok",
  "models": { ... },
  "database": "connected"
}
```

❌ **Se der erro:** Inicie o backend primeiro!
```powershell
cd d:\projetos\Transcricao-de-audio\modules\backend
uvicorn src.main:app --host 0.0.0.0 --port 2020
```

### 3️⃣ Iniciar Frontend (10 segundos)

```powershell
npm run dev
```

**Você verá:**
```
VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### 4️⃣ Abrir no Navegador

🌐 Acesse: **http://localhost:3000**

### 5️⃣ Testar a Aplicação

✅ Você deve ver:
- Dashboard com cards de estatísticas
- Menu lateral com navegação
- Navbar com logo e usuário "Usuário Demo"
- Status dos modelos (Whisper, AssemblyAI, Pyannote)

## 🎯 Primeiro Teste

### Fazer uma Transcrição

1. Clique em **"Nova Transcrição"** no menu lateral
2. Arraste um arquivo de áudio ou clique para selecionar
3. Escolha o modelo (Whisper ou AssemblyAI)
4. Ative/desative a diarização
5. Clique em **"Iniciar Transcrição"**
6. Aguarde o processamento
7. Visualize o resultado!

## 🆘 Problemas Comuns

### ❌ "Cannot connect to backend"

**Solução:**
```powershell
# Verificar se o backend está rodando
curl http://localhost:2020/health

# Se não estiver, inicie:
cd d:\projetos\Transcricao-de-audio\modules\backend
uvicorn src.main:app --host 0.0.0.0 --port 2020
```

### ❌ "Port 3000 is already in use"

**Solução:**
```powershell
# Opção 1: Matar processo na porta 3000
$port = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port) { Stop-Process -Id $port.OwningProcess -Force }

# Opção 2: Usar outra porta
npm run dev -- --port 3001
```

### ❌ "Module not found"

**Solução:**
```powershell
# Limpar e reinstalar
Remove-Item -Recurse -Force node_modules
npm install
```

### ❌ "CORS Error"

**Solução:**
O backend já está configurado com `allow_origins=["*"]`.
Se persistir, verifique se está usando a URL correta no `.env`:
```env
VITE_API_URL=http://localhost:2020
```

## 📋 Checklist de Verificação

Antes de começar a desenvolver, verifique:

- [ ] Node.js 18+ instalado (`node --version`)
- [ ] NPM instalado (`npm --version`)
- [ ] Backend rodando na porta 2020
- [ ] Dependências instaladas (`node_modules` existe)
- [ ] Arquivo `.env` existe
- [ ] Frontend iniciado na porta 3000
- [ ] Navegador aberto em http://localhost:3000
- [ ] Dashboard carregando corretamente
- [ ] Status dos modelos visível

## 🎓 Próximos Passos

Agora que tudo está funcionando:

1. **Explore o Dashboard**
   - Veja as estatísticas
   - Status dos modelos
   - Transcrições recentes

2. **Faça uma Transcrição**
   - Upload de arquivo
   - Escolha do modelo
   - Visualize o resultado

3. **Navegue pela Interface**
   - Lista de transcrições
   - Detalhes de transcrição
   - Configurações

4. **Explore o Código**
   - Leia o `README.md`
   - Veja `PROJECT_STRUCTURE.md`
   - Entenda os componentes

5. **Personalize**
   - Cores (tailwind.config.js)
   - Logo (Navbar.jsx)
   - Usuário (authStore.js)

## 📚 Documentação Completa

- **README.md** - Documentação principal e features
- **SETUP.md** - Guia detalhado de instalação
- **PROJECT_STRUCTURE.md** - Estrutura completa do projeto
- **VISUAL_GUIDE.md** - Guia visual de design
- **COMMANDS.md** - Todos os comandos úteis

## 💡 Dicas

- Use `Ctrl+C` para parar o servidor
- Use `npm run build` para gerar build de produção
- Use `npm run preview` para testar o build
- Mantenha o terminal aberto para ver logs
- F12 no navegador para ver console

## 🎉 Pronto!

Seu frontend está rodando! 🚀

Agora você pode:
- ✅ Fazer uploads de áudio
- ✅ Transcrever com Whisper ou AssemblyAI
- ✅ Usar diarização de falantes
- ✅ Visualizar transcrições
- ✅ Exportar em múltiplos formatos

**Bom desenvolvimento!** 💻
