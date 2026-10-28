# Ajazz Linux ? instala??o em portugu?s

[README principal](README.md) ? [C?digo e licen?a](LICENSE)

O Ajazz Linux ainda n?o possui instalador RPM, Flatpak ou instala??o com um clique. Este guia instala o c?digo do projeto e explica como abrir o aplicativo depois. N?o ? preciso ter conta no GitHub.

## Fedora Workstation / KDE

Abra o aplicativo **Terminal** e execute um bloco por vez, na ordem. Estes passos s?o para instala??es Fedora com `dnf`; Silverblue/Kinoite precisam de outro procedimento. Os pacotes foram conferidos na documenta??o Fedora, mas esta instala??o ainda n?o foi testada diretamente no Fedora. A CI Linux passou no Ubuntu.

### 1. Instalar os pr?-requisitos

```sh
sudo dnf install git python3 python3-pip \
  libglvnd-egl libglvnd-glx libxkbcommon-x11 \
  xcb-util-cursor xcb-util-wm xcb-util-keysyms
```

Digite sua senha de login quando solicitado. Nada aparece enquanto voc? digita a senha; isso ? normal. Confira a lista de pacotes e confirme a instala??o.

### 2. Baixar e instalar o Ajazz Linux

```sh
cd "$HOME"
git clone https://github.com/a32fred/ajazz-linux.git
cd ajazz-linux
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

O projeto fica na pasta `ajazz-linux` dentro da sua pasta pessoal. O download das depend?ncias pode demorar alguns minutos. Mantenha essa pasta, pois ela cont?m o aplicativo e seu ambiente Python. N?o ? necess?rio ativar o ambiente manualmente.

Se j? baixou o projeto, n?o execute `git clone` novamente: entre na pasta existente. Se algum comando der erro, pare nesse ponto; n?o prossiga como se a instala??o tivesse terminado.

### 3. Abrir a demonstra??o

```sh
sh "$HOME/ajazz-linux/run-vela" --demo
```

Uma janela do Ajazz Linux com o aviso **DEMO MODE** deve abrir. Essa demonstra??o funciona sem mouse conectado e sem alterar o dispositivo.

### 4. Liberar o acesso ao mouse real

Feche a demonstra??o. Instale a regra de acesso USB uma ?nica vez:

```sh
cd "$HOME/ajazz-linux"
sudo install -m 644 packaging/linux/70-vela.rules /etc/udev/rules.d/70-vela.rules
sudo udevadm control --reload-rules
```

**Desconecte e reconecte o cabo USB do mouse.** Depois abra o Ajazz Linux sem `--demo`:

```sh
sh "$HOME/ajazz-linux/run-vela"
```

Na janela, clique em **Scan**, selecione o AJ199 e clique em **Read mouse**. Essas a??es leem as configura??es. O bot?o **Apply to mouse** grava suas altera??es. Execute o aplicativo com seu usu?rio normal, sem `sudo`. A grava??o e o funcionamento f?sico do mouse ainda precisam de valida??o.

## Abrir novamente e atualizar

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

H? instru??es para criar um [atalho no menu de aplicativos](README.md#desktop-shortcut-optional).

## Se n?o funcionar

- **A pasta j? existe:** entre nela com `cd "$HOME/ajazz-linux"`, sem clonar de novo.
- **Falta `git`, `python3` ou `pip`:** conclua a etapa 1.
- **Falta `.venv/bin/python` ou aparece `No module named vela`:** a etapa 2 n?o terminou corretamente.
- **Erro `xcb` ou biblioteca gr?fica ausente:** confira os pacotes da etapa 1 e copie o erro completo se persistir.
- **A demonstra??o abre, mas o mouse d? permiss?o negada:** conclua a etapa 4 e reconecte o cabo na sua sess?o de desktop. N?o abra a interface como root.
- **`No matching distribution found`:** anote a sa?da de `python3 --version` e o erro completo. As depend?ncias precisam oferecer vers?es para o seu Python e arquitetura; n?o substitua o Python do sistema.

Se continuar com problema, abra um [relato de erro](https://github.com/a32fred/ajazz-linux/issues/new?template=bug_report.md) com a vers?o do Fedora, o comando que falhou e a mensagem completa. Remova dados pessoais antes de publicar.

Outras distribui??es usam o mesmo ambiente Python e inicializador, mas os nomes dos pacotes mudam. Consulte a [instala??o geral](README.md#other-linux-distributions).

Fontes dos pr?-requisitos: [Python/pip no Fedora](https://developer.fedoraproject.org/tech/languages/python/pypi-installation.html), [EGL](https://packages.fedoraproject.org/pkgs/libglvnd/libglvnd-egl/), [GLX](https://packages.fedoraproject.org/pkgs/libglvnd/libglvnd-glx/), [XKB para X11](https://packages.fedoraproject.org/pkgs/libxkbcommon/libxkbcommon-x11/) e [cursores XCB](https://packages.fedoraproject.org/pkgs/xcb-util-cursor/).
