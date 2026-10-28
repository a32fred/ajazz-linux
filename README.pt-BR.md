# Ajazz Linux: instalação em português

[README principal](README.md) · [Código e licença](LICENSE)

Aplicativo **não oficial** para configurar o mouse AJAZZ AJ199 no Linux: DPI, botões, macros e a luz da roda de rolagem. Não é afiliado nem aprovado pelo fabricante. Esta é uma versão de pré-lançamento: as gravações no mouse foram testadas à mão em uma única unidade (cabo USB).

## Opção 1: instalar por pacote (recomendado)

Baixe os arquivos da sua distribuição na [página de versões](https://github.com/a32fred/ajazz-linux/releases). São dois pacotes, para você não instalar o que não usa:

- **`ajazz-linux-cli`**: comandos de terminal e a regra de acesso USB. Só precisa do Python 3.10 ou mais novo e funciona em qualquer distribuição.
- **`ajazz-linux`**: a janela do aplicativo. Usa o Qt que a sua distribuição já tem, então ocupa bem menos de 1 MB.

| Sistema | Comando |
|---|---|
| Fedora | `sudo dnf install ./ajazz-linux-cli-*.rpm ./ajazz-linux-0*.rpm` |
| Debian 13, Ubuntu 25.10 ou mais novo | `sudo apt install ./ajazz-linux-cli_*.deb ./ajazz-linux_*.deb` |
| Ubuntu 24.04 ou mais antigo | `sudo apt install ./ajazz-linux-cli_*.deb` e, para a janela, `pipx install "git+https://github.com/a32fred/ajazz-linux"` (o Ubuntu 24.04 não traz o Qt 6 para Python) |
| Outras distribuições | `pipx install "git+https://github.com/a32fred/ajazz-linux"` e depois a regra de acesso da Opção 2, passo 4 |

Os pacotes já instalam a regra de acesso USB e a aplicam a um mouse que esteja conectado, então **não precisa desconectar o cabo**. Abra o **Ajazz Linux** pelo menu de aplicativos, ou rode `ajazz-linux` no terminal, sempre com o seu usuário normal, sem `sudo`. Na janela, clique em **Scan**, escolha o AJ199 e clique em **Read mouse**. Só o botão **Apply to mouse** grava no mouse.

A instalação dos pacotes foi verificada em contêineres limpos (Fedora 44, Debian 13, Ubuntu 22.04 e 24.04). Com um mouse real, o uso dos pacotes ainda é tão pouco testado quanto o resto desta versão.

## Opção 2: instalar pelo código-fonte (Fedora)

Use esta opção se não houver pacote para o seu sistema. Abra o aplicativo **Terminal** e execute um bloco por vez, na ordem. Estes passos são para instalações Fedora com `dnf`; Silverblue e Kinoite precisam de outro procedimento. Não é preciso ter conta no GitHub.

### 1. Instalar os pré-requisitos

```sh
sudo dnf install git python3 python3-pip \
  libglvnd-egl libglvnd-glx libxkbcommon-x11 \
  xcb-util-cursor xcb-util-wm xcb-util-keysyms
```

Digite sua senha de login quando solicitado. Nada aparece enquanto você digita a senha; isso é normal. Confira a lista de pacotes e confirme a instalação.

### 2. Baixar e instalar o Ajazz Linux

```sh
cd "$HOME"
git clone https://github.com/a32fred/ajazz-linux.git
cd ajazz-linux
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

O projeto fica na pasta `ajazz-linux` dentro da sua pasta pessoal. O download das dependências pode demorar alguns minutos. Mantenha essa pasta, pois ela contém o aplicativo e o ambiente Python. Não é necessário ativar o ambiente manualmente.

Se já baixou o projeto, não execute `git clone` novamente: entre na pasta existente. Se algum comando der erro, pare nesse ponto e não prossiga como se a instalação tivesse terminado.

### 3. Abrir a demonstração

```sh
sh "$HOME/ajazz-linux/run-vela" --demo
```

Uma janela do Ajazz Linux com o aviso **DEMO MODE** deve abrir. A demonstração funciona sem mouse conectado e sem alterar o dispositivo.

### 4. Liberar o acesso ao mouse real

Feche a demonstração. Instale a regra de acesso USB uma única vez:

```sh
cd "$HOME/ajazz-linux"
sudo install -m 644 packaging/linux/70-ajazz-linux.rules /etc/udev/rules.d/70-ajazz-linux.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw --action=add
```

Depois abra o Ajazz Linux sem `--demo`:

```sh
sh "$HOME/ajazz-linux/run-vela"
```

Na janela, clique em **Scan**, selecione o AJ199 e clique em **Read mouse**. Essas ações leem as configurações. O botão **Apply to mouse** grava suas alterações. Execute o aplicativo com seu usuário normal, sem `sudo`.

### Abrir novamente e atualizar

Para abrir em qualquer outro momento:

```sh
sh "$HOME/ajazz-linux/run-vela"
```

Para atualizar, feche o Ajazz Linux e execute:

```sh
cd "$HOME/ajazz-linux"
git pull --ff-only
.venv/bin/python -m pip install -e .
```

Há instruções para criar um [atalho no menu de aplicativos](README.md#desktop-shortcut-optional).

## Se não funcionar

- **A pasta já existe:** entre nela com `cd "$HOME/ajazz-linux"`, sem clonar de novo.
- **Falta `git`, `python3` ou `pip`:** conclua o passo 1 da Opção 2.
- **Falta `.venv/bin/python` ou aparece `No module named vela`:** o passo 2 não terminou corretamente.
- **Erro `xcb` ou biblioteca gráfica ausente:** confira os pacotes do passo 1 e copie o erro completo se persistir.
- **A demonstração abre, mas o mouse dá permissão negada:** instale a regra de acesso (os pacotes já fazem isso) e reconecte o cabo na sua sessão de desktop. Não abra a interface como root.
- **`No matching distribution found`:** anote a saída de `python3 --version` e o erro completo. As dependências precisam oferecer versões para o seu Python e arquitetura; não substitua o Python do sistema.

Se continuar com problema, abra um [relato de erro](https://github.com/a32fred/ajazz-linux/issues/new?template=bug_report.md) com a versão da distribuição, o comando que falhou e a mensagem completa. Remova dados pessoais antes de publicar.

Outras distribuições usam o mesmo ambiente Python e inicializador, mas os nomes dos pacotes mudam. Consulte a [instalação geral](README.md#other-linux-distributions).

Fontes dos pré-requisitos: [Python/pip no Fedora](https://developer.fedoraproject.org/tech/languages/python/pypi-installation.html), [EGL](https://packages.fedoraproject.org/pkgs/libglvnd/libglvnd-egl/), [GLX](https://packages.fedoraproject.org/pkgs/libglvnd/libglvnd-glx/), [XKB para X11](https://packages.fedoraproject.org/pkgs/libxkbcommon/libxkbcommon-x11/) e [cursores XCB](https://packages.fedoraproject.org/pkgs/xcb-util-cursor/).
