# AJ199 — especificação de comportamento para implementação independente em Linux

> Public edition: personal workspace paths have been generalized. Analysis-only helpers, private captures and original vendor artifacts are not distributed. Function addresses, protocol facts and UNKNOWN markers are retained.


Data da investigação: 2026-10-24. Revisão ampliada com Ghidra e observação REA/Frida. A segunda passagem recuperou seis entradas adicionais de código por message maps e confirmou22 consultas de leitura com22 respostas. Resultados físicos de escrita e compatibilidade Linux continuam delimitados como UNKNOWN. Alvo exclusivo: `C:\Program Files (x86)\AJAZZ\AJ199 Gaming Mouse`. Objetivo: cliente nativo Linux, sem depender de Wine, código, DLLs ou assets do fornecedor. Este documento descreve contratos observados e inferidos; não contém código recuperado nem imagens do produto.

## Como interpretar os requisitos

**OBSERVADO** significa bytes/estrutura estática ou observação passiva identificada; não implica execução de uma função. **INFERIDO** significa interpretação do fluxo de código recuperado. **UNKNOWN** significa que a evidência disponível não estabelece o contrato. Recursos compartilhados podem anunciar funções que o modelo AJ199 não expõe. Não converter um texto de tradução em prova de suporte do hardware.

O pedido de leitura binário a binário é acompanhado de um inventário e cobertura explícita. Ler todos os bytes, analisar funções e demonstrar todos os comportamentos são atividades diferentes. A cobertura final abaixo registra falhas, limites e funcionalidades sem confirmação. Não se declara equivalência completa com o original enquanto houver UNKNOWNs de interoperabilidade.

## Evidências e reprodutibilidade

| Referência | Fonte e alcance |
|---|---|
| E-INV | `resource_inventory.json`: todos os arquivos regulares instalados, tamanho e SHA-256; 79 arquivos, 4.773.689 bytes. |
| E-CFG | `Cfg.ini` instalado, referências por seção/chave e linha; catálogo completo em `RESOURCE_FINDINGS.md`. |
| E-PT / E-SC | `en/text.xml` e `sc/text.xml`, referências por chave XML; catálogo integral com linhas em `RESOURCE_FINDINGS.md`. A pasta en contém português. |
| E-PE | `OemDrv.exe.pe.json`: leitura PE independente, imports com endereço IAT e strings com offset de arquivo. Não é evidência produzida pela REA. |
| E-REA-R | REA `inspect_pe_resources`, Evidence `ev_164cc82b15b6403cd5c17e8a7e71c5430b91a27b629aa768be74bd5f5853d07a`, SHA-256 OemDrv `ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846`, 58 recursos, inventário completo para o parser, payloads em geral opacos. |
| E-GH | Ghidra 12.2 headless, projeto AJ199, base/endereço virtual PE registrados no inventário; endereços de função citados nas seções nativas. Pseudocódigo é interpretação do decompilador, não fonte original. |
| E-RUN | `RUNTIME_FINDINGS.md` e arquivos `runtime_*.json`: processo, módulos, PnP e persistência observados passivamente. Não houve clique, aplicação de configuração ou captura de rede. |
| E-HELP | `HELPER_FINDINGS.md`: DLLs auxiliares e desinstalador, com inventários Ghidra/REA próprios. |

A REA 6.7.0 CLI foi utilizada porque nenhum servidor REA estava conectado. Sua análise nativa recusou o Ghidra fornecido (12.2) com `provider_unavailable/unsupported_version`, aceitando somente 12.1.x; diagnóstico integral em `rea-oem-overview.json`. Nenhuma configuração do cliente, instalação do Ghidra ou política foi alterada para contornar a versão. A análise nativa utiliza diretamente o Ghidra fornecido. REA PE resources funciona sem esse provider. Java existente: Eclipse Adoptium JDK 25.0.4.101.

## Telas, recursos e estados identificados por recursos

Os itens desta seção são requisitos candidatos para paridade. Sua presença nos recursos é OBSERVADA; habilitação por modelo, hierarquia exata e execução são UNKNOWN até confirmação nas seções nativas.

| ID | Tela/entrada → resultado esperado | Evidência | Estado |
|---|---|---|---|
| UI-01 | Navegar entre teclas, DPI, macros e iluminação. | E-PT/E-SC `tc_page1`…`tc_page4` | Candidato |
| UI-02 | Oferecer OK, aplicar, cancelar, restauração geral e redefinição de teclas; distinguir confirmação de exclusão e restauração. | `tc_ok`, `tc_apply`, `tc_cancel`, `tc_restore`, `tc_reset`, `tc_msg5/6` | Candidato; efeitos de cancelar/aplicar UNKNOWN nesta evidência |
| UI-03 | Configuração de idioma; mostrar nome/versão de driver e firmware; sair, minimizar/tray, suporte/página oficial quando habilitados. | E-CFG `Lang1/2`, `Title`, `TrayIcon`; E-PT `tc_config`, `tc_exit`, `tc_version`, `tc_fwver2`, `tc_web`, `tc_msg30`; E-PE strings `Min window`, `LangIndex` | Candidato; tray real UNKNOWN |
| UI-04 | Selecionar perfil atual, importar, exportar, renomear e alternar. | E-PT `tc_msg14`, `tc_msg32`…`tc_msg35`, `tc_prosw` | Candidato |
| KEY-01 | Atribuir esquerdo, direito, meio, voltar/avançar, roda para cima/baixo e duplo clique esquerdo/direito. | `tc_msfun`, `tc_click`…`tc_rdbclick` | Candidato |
| KEY-02 | Atribuir tecla simples, combinação, modificadores/Windows e modos 1/2/3. | `tc_singlekey`, `tc_combokey`, `tc_windows`, `tc_shift`, `tc_mode1`…`tc_mode3` | Candidato; não inferir modo shift do mouse pelo rótulo |
| KEY-03 | Atribuir play/pause, parar, anterior/próxima, volume +/−, mudo. | `tc_PL`, `tc_stop`, `tc_pre_media`, `tc_next_media`, `tc_vol_up/dw`, `tc_mute` | Candidato |
| KEY-04 | Atribuir parar navegador, busca, email, página inicial, explorador, calculadora, atualizar, favoritos e player. | `tc_kbmedia_stop`…`tc_kbmedia_msel` | Candidato; pode ser tecla HID de consumo em vez de lançar programa |
| KEY-05 | Atribuir macro, desativar, DPI +/−/ciclo, três cliques, tiro, iluminação ligar/desligar/alternar, bloqueio DPI, alternar polling/perfil. | `tc_mac_def`, `tc_key_off`, `tc_dpiadd/sub/loop`, `tc_three`, `tc_fire`, `tc_rgb`, `tc_snipe`, `tc_reportsw`, `tc_rgbsw`, `tc_prosw` | Candidato |
| DPI-01 | Estágios DPI, cores por estágio, eixos X/Y, ajuste preciso por duplo clique. | E-CFG DEV_1 `DM=6`, `DPI`, `DC`; `tc_msg19`, `tc_msg266`, `tc_adv_str19/25/26` | Defaults observados; granularidade UNKNOWN |
| DPI-02 | Ajustar polling, debounce, LOD, correção de ângulo e Motion Sync quando expostos. | E-CFG `ShowLOD=1`, `Debounce=8`, `Sensor=0x3395`; `tc_adv_str6/9/13/17/28` | Candidato; valores no fio exigem seção de protocolo |
| SYS-01 | Velocidade do ponteiro, duplo clique, rolagem, página inteira e precisão do ponteiro. | `tc_adv_str1`…`tc_adv_str5`, SC `tc_adv_str18` | Candidato de integração Windows; não tratar como recurso de firmware |
| MAC-01 | Lista de macros/pastas e lista ordenada de eventos; gravar/parar; atraso automático; inserir evento. | `tc_macro_start/stop/list/key_list/auto/loop` | Candidato |
| MAC-02 | Criar pasta/macro, renomear, modificar, excluir, salvar, importar/exportar individualmente e em lote. | `tc_macro_msg3`…`tc_macro_msg22`; E-CFG `MacroDir=1` | Candidato |
| MAC-03 | Eventos pressionar, soltar, atraso; repetição por contagem, até soltar ou até nova tecla. | `tc_macro_msg14/15/16`, `tc_macro_loop1/2/3` | Candidato; tradução de loop3 precisa código |
| LED-01 | Efeitos candidatos: fixo, respiração, fluxo, neon, corrida monocromática, respiração multicolorida, desligado. | `tc_led_mode1`…`tc_led_mode7`; E-CFG `LedOpt1`…`LedOpt7`, `LedMask=0x14` | Subconjunto efetivo UNKNOWN |
| LED-02 | Brilho, velocidade, cor, onda/gradiente, efeito DPI, apagar ao mover e temporizador. | `tc_adv_str7/8/10/11/12/14/20/23/29` | Candidato |
| PWR-01 | Bateria/carregamento, suspensão/economia e firmware. | E-CFG `ShowPower=0`; `tc_fwver2`, `tc_msg27`, `tc_adv_str20/22/24`; nomes power*.png | ShowPower é máscara de bits; bateria100% observada na segunda passagem, ver DR05 |

### Mensagens e condições de erro previstas

| ID | Condição/saída | Evidência; limite conhecido |
|---|---|---|
| ERR-01 | Nome inválido ou nome duplicado. | `tc_tip1`, `tc_macro_msg8`; caracteres/tamanho UNKNOWN. |
| ERR-02 | Abrir arquivo falha ou configuração inválida. | SC `tc_tip2/3`; chaves ausentes em PT, fallback UNKNOWN. |
| ERR-03 | Sem macro/pasta selecionada; exigir parar gravação; máximo de eventos atingido. | `tc_macro_msg1/2/17/18`; máximo UNKNOWN por recurso. |
| ERR-04 | Não remover último clique esquerdo. | `tc_msg1`; PT omite qual botão. |
| ERR-05 | Sem macro: oferecer criação; clique direito edita itens. | `tc_msg9`, `tc_macro_msg9`. |
| ERR-06 | Mouse dormindo/offline: orientar mover ou religar; não detectado/desconectado. | `tc_msg10/15`; conexão física e sono não são equivalentes. |
| ERR-07 | Atualização de configurações em andamento, falha na atualização, aguardar inicialização ou dispositivo incompatível. | `tc_msg12`, SC `tc_msg13`, `tc_adv_str15/16`; PT menciona 10 segundos sem confirmação do temporizador. |
| ERR-08 | Não permitir todos os estágios DPI desligados. | SC `tc_msg28`, ausente em PT. |
| ERR-09 | Limite de combinação de teclas. | SC `tc_msg29` diz 3; PT genérico; confirmar no código. |
| ERR-10 | Mais de um dispositivo: pedir manter somente um. | `tc_msg36`; PnP observou ambos os PIDs, sem prova do comportamento de seleção. |
| ERR-11 | Ligar iluminação antes de ajustar parâmetro. | `tc_adv_str29`. |
| ERR-12 | Debounce reduzido pode causar clique duplo; sugerir 8ms ou aumentar. | `tc_debounce_tips`; aviso textual, não experimento físico. |

### Divergências que a implementação não deve resolver por suposição

E-PT `tc_str2` diz 3–255, E-SC diz intervalo 10–255; faixa/unidade real do tiro: UNKNOWN até código. `tc_adv_str22` significa minutos em SC, mas foi traduzido como “Mínimo” em PT. `tc_key_off` e `tc_shift` também divergem semanticamente. `KM=12` não comprova 12 botões físicos: o loader divide KM por2 e configura seis posições; dez defaults K existem no arquivo. `DR=0x1000` é código interno; UI e codec confirmam1000Hz, sem suporte4000Hz demonstrado. Catálogo completo: `RESOURCE_FINDINGS.md`.

## Persistência observada e formatos candidatos

| ID | Contrato | Evidência/certeza |
|---|---|---|
| STORE-01 | Instalação contém INI com seções OPT/DEV_1 e traduções XML declaradas UTF-16; ler valores conforme o modelo, sem reutilizar os assets. | E-CFG/E-INV/E-PT/E-SC. |
| STORE-02 | Nesta máquina, pasta de estado é `%LOCALAPPDATA%\JM03`. | E-RUN `runtime_config_paths.json`, E-CFG Appdir=JM03. |
| STORE-03 | `lang.ini` tem `[OPT]` e `LangIndex=0`, CRLF; 20 bytes observados. | E-RUN `runtime_config_bytes.json`. |
| STORE-04 | `CID.dct` observado tem 8 bytes `40 00 00 00 01 00 00 00`, compatível com dois LE32 CID/MID. | E-RUN; interpretação dos campos inicialmente inferida. |
| STORE-05 | `PRO_4001.dct` observado tem 8468/0x2114 bytes, nome UTF-16LE `Profile 1` em 0x214. | E-RUN; estrutura completa exige correlação nativa. |
| STORE-06 | Valores salvos diferem dos defaults: candidatos DPI X/Y incluem 1200,500,1500,3200,5000,26000; não sobrescrever com defaults ao abrir. | E-RUN offsets 0x6DC/0x6E0 + 0x10*n, E-CFG DPI. Natureza dos campos inicialmente inferida. |
| STORE-07 | Extensões `.jma` e `.jmm`, e nome `mac.dct`, são usados por rotinas de perfil/macro. | E-PE offsets 0x1B246C,0x1B25AC,0x1B4EE0; existência de strings não estabelece layout. |

Snapshot passivo não atômico; nenhum arquivo foi alterado pelo investigador. Busca de registro foi limitada a subchaves imediatas com nomes AJAZZ/AJ199/JM03/OemDrv e valores Run: nenhum encontrado nesse limite. Não afirmar ausência global de registro/serviço/tarefa. Não confundir arquivo DCT, memória interna e relatório USB.

## Rede e transportes

NET-01: **UNKNOWN** para tráfego de rede efetivamente emitido. Não existe captura HAR/SAZ/PCAP ou requisição observada nesta investigação. A tabela de imports PE de OemDrv não contém WinHTTP, WinINet, WS2_32 ou URLMon (E-PE, busca completa de imports). Isso não prova ausência de rede: carregamento dinâmico, ShellExecute, subprocessos e caminhos não exercitados continuam possíveis. XML inclui rótulo de página oficial; URL não foi visitado.

USB-01: VID 0x25A7 e PIDs FA7B/FA7C são configurados e aparecem presentes no PnP (E-CFG; E-RUN `runtime_pnp_present.json`). Não atribuir automaticamente “cabo” e “receptor” só pelos PIDs. Coleções MI_00/MI_01 incluem mouse, teclado, consumo, sistema e fornecedor; número de coleções não é número de dispositivos físicos.

USB-02: Imports estáticos, posteriormente corroborados por captura REA e consultas reais de leitura, incluem `HidD_SetFeature`, `HidD_GetAttributes`, `HidD_GetPreparsedData`, `HidP_GetCaps`, SetupDi*, ReadFile/WriteFile, eventos e overlapped (E-PE IAT 0x57F1EC/0x57F1F8/0x57F1E4/0x57F1F4). O capítulo de observação registra22 consultas reais e suas respostas; import isolado não é a evidência usada para confirmar execução.

## Requisitos próprios do clone Linux

Estes itens são objetivos de engenharia do usuário, não comportamentos atribuídos ao fornecedor.

| ID | Requisito e critério de aceitação | Origem |
|---|---|---|
| LNX-01 | Implementar cliente nativo; nenhum executável/DLL Windows ou asset do fornecedor necessário para executar. | Pedido do usuário; separação clean-room. |
| LNX-02 | Separar descoberta/transporte HID, codec do dispositivo, modelo lógico de perfis/macros e interface. Backend Linux pode usar hidraw/hidapi; não derivar pacote USB de dump DCT. | Objetivo Linux + E-PE/E-RUN, escolha de projeto proposta. |
| LNX-03 | Declarar matriz de suporte por arquitetura, kernel, acesso a hidraw, ambiente gráfico e empacotamento. “Todos os Linux” é objetivo de portabilidade, não propriedade demonstrada por engenharia reversa em Windows. | Pedido do usuário; validação Linux ainda UNKNOWN. |
| LNX-04 | Manter UI/CLI utilizável com acesso negado/sem dispositivo; explicar permissão e permitir redescoberta. Regras de dispositivo devem limitar VID/PID e interfaces apropriadas. | Escolha proposta para Linux; não observada no Windows. |
| LNX-05 | Guardar estado nativo em diretórios XDG por usuário; importadores dos formatos Windows devem validar tamanho, limites e conteúdo sem interpretar ponteiros serializados como endereços. | Escolha proposta; E-RUN sugere estrutura Windows. |
| LNX-06 | Traduzir ações para capacidades efetivas do mouse. Recursos do Windows (Win+D, Explorer, mouse.cpl, ponteiro/rolagem) exigem política específica de desktop; Wayland/X11 e teclados diferentes precisam validação própria. | E-PT/E-SC/E-PE; compatibilidade Linux UNKNOWN. |
| LNX-07 | Não habilitar escrita de firmware ou operações ainda UNKNOWN como se fossem suportadas. Somente promover um codec a suportado após vetores e comparação de leitura/aplicação. | Necessidade de interoperabilidade verificável, não exigência de copiar fornecedor. |

## Checklist de fechamento

Cobertura de funções nativas, máquinas de estados, layout de comandos, formatos, instalação e validação da especificação: em investigação. O fechamento final registra resultados e lacunas.


## Identidade auxiliar e limites de aparência

`skins/mak.skn` não estabeleceu layout de tela. `0043A590` lê520 bytes, toma offset no byte4 e tamanho no byte20, aplica rotação de byte por3 para recuperar texto; nesta cópia offset71,tamanho24 resulta no título AJAZZ AJ199 Gaming Mouse. `0043A6D0` compara título, e startup usa esse resultado como gate. Decodificação independente dos bytes corrobora a interpretação, mas assinaturas/pilha do decompilador estão imperfeitas. Este mecanismo não precisa ser reproduzido pelo clone Linux com marca e interface próprias. Recursos RT_DIALOG102…106 contêm templates vazios320×200; maioria dos controles é construída dinamicamente. E-REA-R e `dialogs.json` ancoram offsets/tamanhos, sem copiar imagens.


## UI e configuração efetiva

Fonte: export Ghidra `private-analysis/OemDrv.exe.decompiled.txt` e xrefs em `OemDrv.exe.inventory.txt`, consultas por endereço usando `read_function.py`. Toda afirmação deste documento é **estática**, salvo referências explícitas ao relatório runtime. O alvo não foi executado nem acionado para esta análise. A decompilação frequentemente perde argumentos/register calling conventions e marca globals sobrepostos; assinaturas, retornos e variáveis de pilha não devem ser copiados literalmente como especificação C.

### Ranges e defaults efetivos

| Campo | Evidência nativa | Resultado para instalação AJ199 |
|---|---|---|
| DPI sensor3395 | FUN_0040c310 gera520 entradas `50*(i+1)`, depois26100..Sensor3395Max em passo100 | 50..26000 inclusivos, passo50; Sensor3395Max instalado26000, default do loader32000 |
| Debounce | FUN_0040bca0 usa byte baixo de DebounceRange como mínimo e próximo byte como máximo; incrementa/decrementa1 | 0..30 inclusivos; default DebounceRange0x1E00 |
| Debounce reset | FUN_0044dc00 usa DEV.Debounce se diferente de0, senão OPT.Debounce | OPT instalado8; default compilado12; DEV ausente equivale0 |
| Alerta debounce | FUN_0040bca0, decremento quando valor atual<=TipForDebounce e threshold<255 passa por confirmação | TipForDebounce ausente default0; comentário8 no INI não configura8 |
| Macro MinDelay | FUN_0044b7f0 default10 | instalado1; detalhes do editor pertencem à análise de macros |
| MinUIDelay | FUN_0044b7f0 default1 |1 |
| DPI levels/default level | FUN_0044a940 DM default6, DEFLEVEL default0, DPIH default10 | DM6, DEFLEVEL1, DPIH22; DPIH é parâmetro de layout, não limite de DPI |
| DPI defaults | FUN_0044a940 exige quantidade de DPI igual a DM e procura cada valor na tabela do sensor |800,1600,2400,3200,5000,26000, todos membros da tabela3395 |
| Cores por DPI | FUN_0044a940 aceita DC somente se número de componentes=DM*3 |6 tripletos RGB instalados |
| Taxa USB defaults | FUN_0044a940 lê RATE1..4 defaults0x125,0x250,0x500,0x1000 e DR default0x500 | DR instalado0x1000; esses números são códigos armazenados, não valores Hz decimais diretamente |
| Sleep | FUN_0044a940 SleepTime default60, SleepTimeCheck1 | sem override instalado;60 segundos, conforme fechamento por00419D00/004197E0 |
| Bancos de teclas | FUN_0044a940 aceita MDNUM3/6/9 e converte para1/2/3; KM precisa ser par, KM/2 entre1..16 | MDNUM ausente9=>3 bancos; KM12=>6 posições configuradas |

Outras validações do loader: DpiLimit exige quantidade par e é distribuído em pares; DPIRANGE exige ao menos3 números e suporta um segundo segmento quando há mais3; DPISET e DPIHW têm suas quantidades comparadas. Warnings literais incluem `wrong DpiLimit value`, `Wrong DPIRANGE`, `DPISET Num != DPIHW Num`, `DPI != DM.`, `DC != DM.`, `Wrong default dpi value`, `Key num to small`. Não implementar validação de entradas arbitrárias imitando acessos sem limite da decompilação: são limitações do original, não requisitos do clone.

### Habilitação por configuração

FUN_0044b7f0 lê OPT e FUN_0044a940 lê DEV_n. Ausência significa os defaults abaixo, não false:

| Flag | Default | Efetivo AJ199 |
|---|---:|---:|
| ApplyNow |0|1|
| GoWithNoDev |0|0|
| ShowProfile/ShowMacro/ShowSys |1|1|
| ShowFWUpdate/ShowMotionSync |0|0|
| ProSwitchEnable |1|1|
| InitOnReset |0|0|
| ShowLOD |0|1|
| ShowUsbRate/ShowRipple/ShowFixLine |1|1|
| ShowMainEffect/ShowLogoEffect |1/0|1/0|
| ShowDebounce |1|1|
| ShowXY |0|0|
| ShowRGBSw |1|1|
| ShowSleep/ShowAutoSleep |1/0|1/0|
| DpiColorReadOnly |0|0|
| ShowDpiColor/ShowDpiLED/ShowDpi |1|1|

ShowDpi=0 força ShowDpiLED=0 no loader. FUN_00408840 efetivamente oculta os controles de sistema se ShowSys=0, oculta os controles DPI quando DEV.ShowDpi=0 e oculta oito controles XY se ShowXY=0 ou o modo XY do perfil está desativado. Isto é comportamento de branch estático; não foi demonstrada a aparência de cada controle nesta sessão.

ShowPower é lido duas vezes em FUN_0044b7f0 para globals diferentes, com defaults0 e1. O override explícito instalado0 zera ambos. Não unificar esses globals em uma inferência sobre todas as variantes OEM.

#### Taxa e subconjunto LED corroborados

FUN_00403420 formata labels com `%d Hz`, usando tabela125,250,500,1000; FUN_00435120 contém o mesmo formato. FUN_00408750 seleciona quatro controles com os códigos0x125,0x250,0x500,0x1000. Assim os labels são125/250/500/1000Hz, enquanto os códigos armazenados têm dígitos decimais representados em hexadecimal, e não devem ser convertidos diretamente para inteiro decimal. O último literal1000 foi recuperado como float1.4013e-42 na variável de pilha; são os mesmos bits0x000003E8, não uma quinta taxa.

FUN_00418470 popula combo LED em sete índices0..6 e só adiciona quando `(LedMask & (1<<índice)) == 0`. Portanto LedMask é uma **máscara de exclusão**. Valores associados são1,2,3,4,5,6,0; com LedMask0x14 exclui modo3 e modo5, mantendo1,2,4,6,0. Os sete textos candidatos são globals0060D5A8..0060D5C0; a sequência de recursos XML tc_led_mode1..7 traz Fixo, Respiração, Fluxo, Neon, Fluxo de cor única, Respiração colorida, Desligado. A correspondência sequencial sugere que a UI AJ199 oferece Fixo/Respiração/Neon/Respiração colorida/Desligado. O teste da máscara, IDs e associação individual ao texto foram confirmados pelo assembly do loader XML, registrado ao final.

FUN_0041a250 usa LedOpt do modo selecionado para ocultar/mostrar controles de brilho, velocidade e cor. Quando troca modo com param2!=0, atualiza os limites/defaults de brilho/velocidade do perfil a partir dessa tabela. Não mostrar todo controle em todo efeito no clone.

### Modelo de páginas e eventos

FUN_0043d950 tem quatro destinos numéricos. Antes de trocar página fecha um popup e bloqueia troca quando um filho no offset0x92B8 indica atividade no offset0x1478. Oculta cinco filhos, limpa estado de quatro botões e exibe:

| Página | Filhos exibidos no objeto principal | Refresh observado no código |
|---|---|---|
|1|+0xD24|FUN_004143d0: seleção de banco de teclas0/1/2, debounce e opção associada|
|2|+0x92B8|Editor macro; pode impedir navegação durante gravação/atividade|
|3|+0xD28 e+0xD2C|FUN_00408840 / FUN_00439990; DPI, flags avançadas e painel complementar|
|4|+0xD30|FUN_0041ab00; LEDs/configurações associadas|

Os rótulos traduzidos das páginas devem vir da análise de recursos. O switch é forte evidência da estrutura de navegação, mas não prova a ordem visual final ou nomes em todas as línguas. FUN_0043e7b0 encaminha comandos dos quatro botões para esses destinos. FUN_0043eae0 consome mensagens de tecla para Enter, Escape, Space e F1 antes de PreTranslateMessage; não assumir que Enter aplica e Escape fecha.

FUN_0043e340 altera índice de idioma, recarrega `<instalação>\<idioma>\text.xml`, chama refresh de texto FUN_0043db40 e persiste OPT/LangIndex em lang.ini. FUN_0044b7f0 lê Lang1..n como pares nome,diretório separados por vírgula e rejeita par inválido. AJ199 declara English/en e chinês simplificado/sc.

### Startup, edição, apply, reset e saída

1. **Startup estático:** FUN_0043a7b0 inicializa controles, MFC e GDI+, resolve diretório do executável, carrega XML e chama FUN_0044d070. Este zera o bloco de configuração, lê limites de sensores, gera tabelas em FUN_0040c310, carrega OPT/DEV e constrói defaults. Inicializa parâmetros de macro: mínimo herdado,0x180,0x10,0xFF,0x46 e0xFFFF, cuja semântica cabe à análise de macros.
2. **Instância única:** startup verifica título pelo mecanismo mak.skn já descrito na análise principal; usa mutex `MUTEX_JM_WIRELESS`. ERROR_ALREADY_EXISTS leva a FindWindow por título e PostMessage0x46C com lParam0x202. Caso novo cria o diálogo principal e o abre modalmente.
3. **Gate de edição:** FUN_0043f070 retornafalse se DAT_005dd020=0. Procura entradas de dispositivos em stride0x440; sem entrada só permite se GoWithNoDev!=0. Com ApplyNow=0 ou GoWithNoDev!=0 permite; caso contrário exige retorno1 de FUN_00450ab0. Falha chama FUN_0042ca20. Não interpretar essa função como permissão do sistema operacional: é gate de disponibilidade/estado interno.
4. **Mudança imediata:** FUN_0040bca0 atualiza debounce no objeto de perfil e controles associados. Com ApplyNow!=0 chama FUN_004140c0 ou código equivalente que atribui operação0x1000 ao global de trabalho, zera parâmetro e libera semáforo. Esse caminho demonstra que atualizar UI é separado da thread de envio. O significado da operação0x1000 e sua reconciliação USB pertencem à análise principal.
5. **Refresh:** FUN_0043c4c0 chama quatro grupos de refresh a partir do perfil atual: teclas/debounce, DPI/avançado, painel complementar e LEDs. FUN_00408840 copia valores do modelo para sliders, cores, dropdowns e checkboxes; não significa que valores foram lidos do mouse nesse momento.
6. **Reset:** FUN_0043e410 passa pelo gate, mostra confirmação, seleciona perfil via FUN_0044dec0, chama FUN_0044dd80 e refresh. FUN_0044dd80 limpa área+8 de0x208 bytes, aplica nome padrão, banco atual0, copia três bancos de0x180 bytes e chama FUN_0044dc00. Este zera settings e aplica defaults de configuração: DPI X=Y, cores, flags padrão, debounce, taxa, sleep, LEDs. Não há prova de factory reset independente no firmware só pelo botão de reset UI.
7. **Saída:** FUN_0043e7b0 usa ExitType e TrayIcon para distinguir fechamento e ocultação/minimização; Close com ExitType0 chama FUN_0043bda0. Esta fecha popup, informa status0 ao driver se conectado, fecha janela auxiliar `OemDrvMsgTopWindow`, mata timer0xF5 quando ativo, chama cleanup, salva perfis e CID, oculta janela e posta WM_CLOSE. Isso confirma que tray/minimize não devem ser confundidos com término do processo.

### Persistência DCT confirmada no código

FUN_0043c330 cria/trunca `%sPRO_%02x%02d.dct`, escreve4 bytes de `perfil_atual+4` e depois até4 blocos de perfil, cada um com0x844 bytes, percorrendo lista DAT_005dee00. Logo o arquivo observado8468 bytes é exatamente4+4*0x844. O prefixo não foi identificado como magic e contém um campo do perfil atual. O nome e os bindings no primeiro perfil ficam em arquivo+0x214 e+0x240, correspondendo a memória+0x210 e+0x23C. Cada perfil seguinte começa4+i*0x844, não em um offset descoberto por busca de strings.

FUN_0043bea0 salva CID.dct com8 bytes. A recuperação de argumentos de pilha não é confiável para identificar ambos os campos exclusivamente por essa função; os bytes observados e Cfg.ini corroboram CID0x40/MID1. FUN_0043c330 usa MID decimal no nome ao salvar; o inventory também contém formato `%02x%02x` em outro caminho de leitura, relevante para compatibilidade com MID>=10.

### Configurações do sistema versus dispositivo

FUN_00428950 usa SystemParametersInfo para aceleração Windows e velocidade do ponteiro; FUN_00428a30 usa tempo de duplo clique, linhas por scroll e configuração de rastro, e notifica WM_SETTINGCHANGE. São ações no sistema hospedeiro, não prova de comandos HID. No Linux, essas opções exigem backend específico do ambiente/compositor; não as enviar automaticamente como comandos do mouse. Os valores discretos foram fechados no capítulo de análise dirigida, incluindo ponteiro, duplo clique e rolagem.

### Cobertura e lacunas

Respondidos: DPI3395 e debounce ranges; defaults/overrides e validações centrais; quatro destinos de página; gate de edição; fila de apply; reset do modelo; idioma; saída e estrutura de persistência. Complementado na segunda passagem: handlers de hotplug/behavior, ranges de sistema/LED e bindings MFC. A resposta física e todos os parâmetros ainda não interpretados permanecem delimitados nos capítulos adicionais. Rede tem observação limitada de APIs; quatro destinos de navegação foram observados por Win32/PrintWindow. Semântica física de todos os campos e aplicação/reset completos permanecem UNKNOWN. Para USB e macros consultar os relatórios próprios; não ampliar claims a partir de strings.

### Fechamento dirigido por assembly

Foi aberto o projeto Ghidra salvo com `-process OemDrv.exe -noanalysis -readOnly`; `private-analysis/ui-targeted-assembly.txt` preserva o assembly das funções00430160,0043DB40,0043D950,00418470 e00403420. Não houve execução do mouse/driver, nem alteração do projeto salvo.

#### Índice de texto não é índice de navegação

Loader00430160 mapeia tc_page1->0060D42C (push004309AC/assignment004309E1), tc_page2->0060D430 (00430A1D/00430A52), tc_page3->0060D434 (00430A8E/00430AC3), tc_page4->0060D438 (00430AFF/00430B34). Os valores XML atuais são Configurações de Teclas, Configurações de DPI, Macro e Iluminação.

O consumo observado de D42C é pintura de heading da página de teclas; D430 é heading de DPI pintado por00435120. D434 e D438 não apresentam consumo funcional na decompilação completa além de construção, carga e destruição. A navegação usa imagens navi1..4 em0043C960 e o switch0043D950, não uma tabela indexada diretamente por tc_page*. Portanto a especificação deve manter destinos internos1=teclas,2=editor macro,3=DPI/avançado,4=LED, sem renumerá-los a partir dos sufixos XML. O filho do destino2 é o editor que pode bloquear troca durante atividade; sua identificação também é corroborada pelo refresh0041CE80 e análise própria de macros.

#### LED nomes confirmados individualmente

Assembly de00430160 confirma sete pares, removendo a ressalva de associação apenas sequencial acima: tc_led_mode1->0060D5A8 em0043422C/00434261; mode2->D5AC em0043429D/004342D2; mode3->D5B0 em0043430E/00434343; mode4->D5B4 em0043437F/004343B4; mode5->D5B8 em004343F0/00434425; mode6->D5BC em00434461/00434496; mode7->D5C0 em004344D2/00434507. Assim os modos disponíveis1/2/4/6/0 do combo principal são definitivamente Fixo, Respiração, Neon, Respiração colorida e Desligado com este XML.

#### LOD e sleep

00403420 possui três controles LOD; assembly00403E4D..00403E53 formata índice+1 com `%d mm` quando o texto customizado está vazio. Logo os labels padrão são1mm/2mm/3mm. Três labels não bastam para provar suporte firmware a3mm:00408840 só sincroniza explicitamente seleção para valores1 e2 no trecho recuperado. A lista exata de valores aceitos pelo protocolo deve manter essa ressalva.

00419D00 e004197E0 criam/atualizam opções SleepVal: abaixo60 exibem valor com texto0060D630; a partir60 dividem por60 e usam0060D628. Loader00430160 começa tc_adv_str1 em0060D5D4 e avança4 por texto; logo D630 é str24 (Segundo) e D628 é str22 (traduzido literalmente Mínimo no XML atual, contexto de minutos). Isso confirma armazenamento em **segundos**, default60 segundos. Lista compilada de11 valores em0044A940:10,30,60,300,600,900,1200,1500,1800,2100,2400 segundos. Não copiar o erro de tradução Mínimo para a unidade de tempo do clone.

#### Máquina de sincronização observável no código

0043DE00 trata timers:0xF6 decrementa retries e chama descoberta0040D6C0; cancela timer quando descoberta>0 ou retries acabam.0xF9 verifica DAT_00605B0C e, se>1, alerta e posta WM_CLOSE.0xFA obtém dispositivo0040DAF0, guarda handles nos offsets principais92E0/92E4, chama refresh de layout0043DFB0, informa estado quando janela visível e inicia thread0043B840.0xF2 chama0043B760, que consulta bateria004518E0, aceita percentual<101 e atualiza UI de carga. ShowPower0 não oculta a bateria: é máscara de bits, conforme DR05 e0043B760/00446AF0.

Thread0043B840 marca atividade, adquire lock global, põe DAT_005DD020=0 para bloquear gate de edição, consulta perfil ativo00450B40 e aceita índices0..3. Copia bloco de perfil de0x844 bytes para buffer temporário0060B388, chama leitura0040F660 e só em sucesso copia de volta, troca perfil corrente0060BC08, salva DCT e posta mensagem0x437. Ao final restaura DAT_005DD020=1 e sinaliza evento principal+92BC. Isso separa perfil local anterior de snapshot confirmado no dispositivo e oferece um modelo de estado útil para o clone: descobrindo -> sincronizando/edição bloqueada -> pronto ou leitura falhou. Os handlers e seus bindings MFC foram recuperados na segunda passagem:0043DC20,0043EBC0 e0043B970; ver capítulo de fechamento dirigido.


## Máquinas de estado e fechamento de cobertura

As transições abaixo são inferidas do código estático. Elas descrevem estados lógicos; não estabelecem a aparência exata ou observação de execução. UNKNOWNs não são transições presumidas.

### SM-APP — ciclo do aplicativo

| Estado | Entrada/condição | Ação/saída e próximo estado | Evidência |
|---|---|---|---|
| Inicializando | Início de processo | Inicializar MFC/GDI+, carregar configuração e XML; validar identidade de título |0043A7B0,0044D070,00430160,0043A590/0043A6D0|
| Inicializando | Configuração inválida | Mensagem Data Init failed; não prosseguir ao diálogo normal |0043A7B0|
| Inicializando | Mutex já existe | Procurar janela pelo título, postar0x46C/lParam202; encerrar esta instância |0043A7B0, string MUTEX_JM_WIRELESS|
| Descobrindo | Timer0xF6 | Enumerar/parear HID, reduzir tentativas; concluir ou cancelar ao esgotar |0043DE00,0040D6C0|
| Descobrindo | Modelo encontrado | Guardar handles, atualizar layout, iniciar sincronização |0040D1D0,0043DE00 timerFA,0043B840|
| Descobrindo | Mais de um candidato aceito | Alerta e fechamento pelo guard timerF9 |0043DE00; seleção/priority de PID no capítulo HID|
| Sincronizando | Início de leitura | Bloquear gate005DD020, consultar perfil0..3 e ler para temporário |0043B840,00450B40,0040F660|
| Sincronizando | Leitura bem-sucedida | Commit de0x844 bytes, selecionar perfil, salvar, postar0x437; pronto |0043B840|
| Sincronizando | Falha de leitura | Não fazer commit no caminho de sucesso; restaurar gate e sinalizar término |0043B840; mensagem/recuperação automática completa UNKNOWN|
| Pronto | Editar com ApplyNow1 | Alterar modelo local, enfileirar máscara de operação e sinalizar semáforo; aplicando |004140C0,0040BCA0,00410EE0|
| Pronto | Gate fechado/sem conexão válida | Bloquear edição e mensagem |0043F070,0042CA20; GoWithNoDev0 instalado|
| Aplicando | Operação por máscara | Escrever apenas grupos selecionados; progresso por PostMessage; ACK/retry conforme protocolo |00410EE0,00450DC0,0044FEE0|
| Aplicando | Erro | Falha registrada e/ou aviso; atomicidade/rollback completo UNKNOWN |00410EE0,00450DC0; original pode avançar chunks sem ACK|
| Pronto | Minimizar/ocultar | Informar status quando conectado; minimizar ou esconder conforme ExitType/TrayIcon |0043E7B0|
| Oculto | Ativar instância/tray | Fluxo de mostrar/foreground existe; sequência integral de eventos tray UNKNOWN |0043BD30,0043A7B0|
| Pronto/Oculto | Sair | Fechar popups/auxiliar, status0, parar timers/threads, salvar perfil/CID, WM_CLOSE |0043BDA0,0043C330,0043BEA0|

Hotplug/behavior foram resolvidos estaticamente por seus registros MFC, handlers0043DC20/0043EBC0 e complemento de sincronização0043B970; o capítulo dirigido descreve todas as seis categorias. Não foram exercitados fisicamente sono/retomada e desconexão. Não transformar uma notificação genérica em uma transição física confirmada.

### SM-NAV — navegação e popups

Destino interno1=teclas,2=macro,3=DPI/avançado,4=iluminação; IDs de texto tc_page* não têm a mesma ordem do switch. `0043D950` oculta filhos anteriores, atualiza seleção dos quatro botões e mostra filhos do destino. Antes disso fecha popup e recusa troca se editor macro estiver ativo (+1478), apresentando mensagem. `0043E7B0` despacha cliques. Enter/Escape/Space/F1 são consumidos por0043EAE0; significado de aplicação/fechamento automático por essas teclas: UNKNOWN. Sobreposição de popup, perda de foco, cancelamento e geometria pixel a pixel: parcialmente desconhecidos; não reutilizar skins.

### SM-MAC — editor de macro

| Estado | Evento | Resultado | Evidência |
|---|---|---|---|
| Sem seleção | Gravar/editar/exportar | Solicitar seleção de macro ou pasta conforme ação |0041DE30,00421990; XML tc_macro_msg1/2|
| Selecionada/limpa | Começar gravação | Ativar captura Windows; bloquear operações que exigem parar |0041F330,00421FE0; XML tc_macro_start/stop/msg17|
| Gravando | KeyDown/Up, modificadores, evento suportado | Normalizar tipo, inserir evento, atraso automático, descartar duplicado consecutivo |00421FE0,0041F330|
| Gravando | Limite de eventos | Avisar máximo; máximo inicial70 excluindo linhas de atraso |0041F2B0,0044D070; XML tc_macro_msg18|
| Gravando | Parar | Voltar à edição; representação exata de foco/tecla de parada UNKNOWN |Textos e flags do editor; transição concreta parcial|
| Editável | Inserir/modificar/excluir evento/atraso | Alterar lista, marcar dirty e normalizar |00420220,00420F80,004212D0|
| Dirty | Salvar/flush | Remover flags dirty altas, serializar834 bytes, rotacionar e escrever .jmm |00422660,00422D90|
| Dirty | Falha caminho/escrita | Log de erro; recuperação/rollback do arquivo anterior UNKNOWN |00422660|
| Selecionada | Importar | Exigir834 bytes, decodificar/magic/compatibilidade, gerarID e salvar no destino |00421990,00422200|
| Selecionada | Exportar | Copiar .jmm existente ao destino |00421E20|

Modos de reprodução pertencem ao hardware e têm contrato de arquivo/código, mas não foram exercitados. “Até qualquer tecla” é tradução existente e não prova quais teclas/eventos o firmware usa para interromper.

### SM-PRO — perfil e persistência

Quatro blocos locais podem ser salvos; índice de perfil consultado ao dispositivo deve ficar0..3 (`0043B840`, `0043C330`). Selecionar perfil aciona cmd10 (`00450CE0`). Renomear, importar, exportar, restaurar são ações com seus próprios estados de confirmação/erro. Import JMA pode substituir macro local de mesmo ID e criar outras, depois aplicar perfil; não é import puramente isolado (`0043F390`, `0043F880`). Export coloca índice DPI corrente no bloco e anexa até dez slots de macro (`0043F120`). Reset UI restaura modelo a defaults e pede confirmação (`0043E410`, `0044DD80`), sem prova de factory reset interno independente. Falha durante gravação e retorno após cancelamento têm contrato incompleto: UNKNOWN.

### SM-LED — disponibilidade dos controles

Modos principais efetivos1/2/4/6/0: fixo, respiração, neon, respiração colorida e desligado. `00418470` exclui bits de LedMask0x14; loader00430160 confirmou cada nome. `0041A250` escolhe controles de brilho/velocidade/cor conforme LedOpt do modo, atualizando limites/defaults quando a mudança é do usuário. Luz geral desligada pode bloquear ajustes com aviso (`tc_adv_str29`). Todos os ranges de parâmetros, dinâmica visual física e transições de efeito no mouse: UNKNOWN além do que foi explicitado. ShowLogoEffect0,ShowMotionSync0,ShowPower0 e ShowFWUpdate0 não devem virar recursos visíveis só pela existência de recursos compartilhados.

### Lista de fechamento e lacunas

| Pergunta original | Cobertura obtida | Pendência explícita |
|---|---|---|
| Binário por binário |4 PEs importados/analisados/exportados; 17104 funções reconhecidas tiveram pseudocódigo retornado |Seis entradas adicionais recuperadas a partir de message maps; continua sem prova de ausência de código não reconhecido/indireções|
| Cada arquivo instalado |79 hashes e tamanhos, leitura integral dos bytes para hash; textos/INI completos, DAT parser integral |Conteúdo de imagens não interpretado como contrato visual; nada reutilizado|
| Telas/recursos |4 destinos, editor, popups, perfis, controles condicionais, catálogo de menus |Quatro destinos runtime observados; geometria completa, renderização owner-drawn e diálogos raros UNKNOWN|
| Estados/entradas/saídas |Máquinas principais acima e codecs nos capítulos próprios |Hotplug/behavior fechados estaticamente; todos os caminhos físicos/cancelamentos raros ainda não demonstrados|
| Arquivos |DCT, JMA, JMM, cache mac.dct, idioma, INI/XML, DAT; formatos/tamanhos/validações descritos |Todos os corpos IFPS presentes decodificados; binding original de AfterInstall, campos opacos e arquivos antigos UNKNOWN|
| Protocolos |Descoberta HID,17 bytes, comandos/EEPROM/macros/combos/checksums, capacidades reais passivas |22 consultas de leitura com respostas reais; escrita EEPROM, rádio, bootloader e firmware permanecem sem validação|
| Settings/persistência |Defaults versus overrides versus snapshot;4 perfis, diretório JM03, autostart por atalho |Atomicidade de gravação/recuperação e todos os campos de estrutura UNKNOWN|
| Erros |Validações de arquivo/nome/limites, mensagens, timeouts/retries, ausência/múltiplos dispositivos |Exercício de cada erro runtime e resultados físicos UNKNOWN|
| Linux nativo |Contratos e escolhas de arquitetura para implementação própria |Nenhum clone implementado/testado nesta tarefa; suporte a distribuições/arquiteturas UNKNOWN|

Não confundir100% de funções reconhecidas decompiladas com100% de comportamento demonstrado. As lacunas acima são parte da especificação e precisam permanecer visíveis para quem implementar.

### Validação necessária antes de declarar compatibilidade Linux

Esta é uma proposta de validação futura, não uma tarefa já executada: comparar relatórios do original em ambiente controlado com operações isoladas; confirmar readback de DPI baixo/alto/XY, cores, LOD, debounce, polling, LEDs, perfil e macros; testar falha no meio de escrita, reconexão, sono e desligamento; confirmar a divergência de DPI em lote antes de reproduzir ou corrigir; validar arquivos de importação com vetores e limites; testar hidraw/permissões/hotplug em kernels e arquiteturas declarados, X11/Wayland e desktops escolhidos. Cada UNKNOWN só pode virar requisito confirmado com nova evidência identificada. Não há promessa técnica demonstrável de funcionamento em literalmente todos os Linux a partir de análise Windows.


## Handlers recuperados e controles detalhados

Análise estática adicional em 24/10/2026. Fontes: `inputs/OemDrv.exe`, export integral anterior, `private-analysis/deep-ui-assembly.txt`, `deep-ui-recovered.txt`, `deep-ui-final-asm.txt`, `deep-ui-behavior.txt` e `ui-targeted-assembly.txt`. Ghidra 12.2 abriu o projeto AJ199 com `-process OemDrv.exe -noanalysis -readOnly`. Funções ausentes foram temporariamente criadas **somente em endereços referenciados pela tabela de mensagens MFC**, e as mudanças foram descartadas ao fechar. O executável e o dispositivo não foram executados/escritos por esta análise.

### Lacuna estrutural encontrada

O export anterior de 12.490 funções reconhecidas não cobria todo o código de aplicativo. O binário contém entradas de message map que apontam para rotinas ainda não reconhecidas. A ausência de xref de string no inventory anterior não significava ausência de handler ativo. O novo script `DeepUi.java` encontrou os ponteiros brutos e recuperou os handlers relevantes; isso invalida uma leitura de “100% das funções exportadas” como “100% dos handlers existentes”.

Cada registro MFC abaixo tem seis DWORDs: mensagem, código, primeiro ID, último ID, assinatura, função. Os endereços de registro foram lidos dos bytes PE; o endereço da função fica em registro+0x14.

| Registro VA | Mensagem | Handler | Resultado |
|---|---|---|---|
|005B26C0|0219 WM_DEVICECHANGE|0043DC20|Hotplug recuperado|
|005B26D8|07EB|0043EBC0|Notificações de comportamento recuperadas|
|005B26F0|0477|0043E150|Fechar/destruir popup pendente|
|005B2708|0437|0043B970|OnSyncOk recuperado|
|005B2720|043F|0043BC30|Ação de seleção DPI/LED por mensagem|
|005B2738|0800|0043BBE0|Texto de progresso e operação 8|
|005B2750|0801|0043BA10|Texto de progresso por categoria|
|005B2768|0802|0043BA00|Consultar gate de edição|
|005B2780|07F5|0043B800|Agendar confirmação de descoberta|
|005B2678|046C|0043E250|Callback do tray|
|005B2690|WM_COMMAND ID6000|0043BD30|Mostrar janela|
|005B26A8|WM_COMMAND ID6001|0043BDA0|Encerrar|

Os registros hotplug/behavior/sync têm campos intermediários 0,0,0 e assinatura 0xE. A tabela confirma dispatch, além do nome inferido pela mensagem de log.

### Hotplug e sincronização: resolvido estaticamente

`0043DC20` constrói duas substrings `USB#VID_%04x&PID_%04x` com VID configurado e os dois PIDs configurados. Só processa chegada 0x8000 ou remoção 0x8004 cujos nomes, a partir de lParam+0x1C, contenham uma dessas substrings sem distinção de caixa.

Na chegada, configura cinco tentativas. Na remoção com handle atual, espera 600 ms e chama `004120F0` para consultar versão. Se ainda responde, retorna 1 imediatamente, sem forçar desconexão. Se falha com GetLastError=0x48F, configura uma tentativa, chama `00450280` com objeto principal+92C0 e oculta filho principal+D20. Falhas diferentes não recebem essa mesma ação especial. Se não existe timer F6 e tentativas>0, agenda F6 a cada 1500 ms. Portanto remover um dos nós USB não equivale automaticamente a desconectar o dispositivo selecionado.

Mensagem 0x7F5 → `0043B800`: se ainda não existe timer FA, agenda confirmação após 300 ms. Timer FA já documentado resolve handles e inicia thread de snapshot. Mensagem 0x437 → `0043B970`: atualiza filhos de teclas, DPI/avançado e LED; consulta bateria imediatamente e cria timer F2 a cada 30.000 ms, se ainda ausente. Isso fecha os agendamentos FA/F2 que antes permaneciam desconhecidos.

### Behavior: seis entradas recuperadas

`0043EBC0` exige perfil corrente, configuração de sensor e handle principal+92E0 válidos. wParam transporta o valor; lParam seleciona a categoria:

| lParam | Contrato estático |
|---|---|
|1|Aceita índice DPI >=0 e menor que sensor+0x10; atualiza DAT_005DD018, compõe `DPI-n`, valor escalar ou X/Y conforme sensor+634, mostra aviso auxiliar se os dois gates estiverem ativos e sincroniza seletores dos filhos +D28/+D2C.|
|2|Atualiza seleção de polling nos filhos; wParam1/2/4/8 grava perfil+6BC respectivamente 0x1000/0x500/0x250/0x125. Valores diferentes não alteram esse campo.|
|3|Compara GetTickCount com timestamp de reset principal+92B4; diferença assinada <5000 ms é ignorada como notificação do próprio reset. Após janela, pode mostrar aviso e inicia `0043B840` para reler snapshot.|
|4|Se efeito principal habilitado, espera 10 ms, lê tipo8 com `00451120`, decodifica `00410050` e atualiza página LED quando sucesso.|
|5|Se efeito de logo habilitado, espera 10 ms, lê tipo10, decodifica `004102C0` em perfil+7F8 e atualiza LED quando sucesso.|
|6|Se LED DPI habilitado, espera 10 ms, lê tipo6, decodifica `00410010` e atualiza filhos DPI quando sucesso.|

Não há rollback adicional nem mensagem de erro nesses três ramos de readback se a consulta falha. A interpretação física de cada notificação e a origem real do remetente continuam dependentes de backend/protocolo; o dispatcher por si só não demonstra tráfego observado.

### Sliders e configurações Windows

`00404F20`, assembly 004066D6..00406929, e o mapeamento reverso de `00409240` fecham os valores selecionáveis:

| Opção | Valores gravados no modelo | Campo |
|---|---|---|
|Velocidade do ponteiro|1,2,4,6,8,10,12,14,16,18,20|perfil+6C8|
|Duplo clique|900,830,760,690,620,550,480,410,340,270,200 milissegundos|perfil+6C4|
|Rolagem|1..10 linhas; checkbox página inteira substitui por 0xFFFFFFFF|perfil+6C0|
|Precisão/aceleração|booleano|perfil+6CC|

Os sliders possuem posições discretas; não implementar o ponteiro como todos os inteiros de 1 a20 nem duplo clique como qualquer valor entre200 e900. A tabela de ponteiro é copiada em 00406743..004067D4; a de duplo clique em 00406830..004068C1. Scroll usa slider de dez posições e leitura sem tabela de valores nesse controle (`00409240`).

`00428950`: aceleração desligada escreve tripla Windows (0,0,0), ligada escreve (6,10,1), somente quando a configuração atual difere ou leitura falha. Velocidade usa SPI_GETMOUSESPEED/SETMOUSESPEED 0x70/0x71. `00428A30`: duplo clique SPI_SETDOUBLECLICKTIME0x20; linhas0x68/0x69; rastro0x5E/0x5D. Flags3 persistem/notificam a mudança. Rastro em perfil+6D0 tem default0; nenhum slider de rastro efetivamente associado foi confirmado aqui. Isso é configuração do host e não comando HID.

### LED: limites, defaults e disponibilidade

Correção conceitual: os primeiros valores de `LedOpt` usados por `0041A250` são **defaults aplicados na troca de modo** e também determinam se os controles aparecem. Não são, por essa função, limites máximos variáveis por modo. `0044A190` inicializa slider com mínimo1 e máximo passado pelo chamador; `00418470` passa10 para brilho principal (+758, chamada00418DC5) e velocidade principal (+1CFC,004190BB). Assim ambos têm posições1..10; modo que não usa um parâmetro pode manter0 no modelo com controle oculto.

| Modo principal | ID | Velocidade default +7C4 | Brilho default +7C8 | Cor RGB editável |
|---|---|---|---|---|
|Fixo|1|0/oculta|6|Sim|
|Respiração|2|6|6|Sim|
|Neon|4|6|6|Não|
|Respiração colorida|6|6|6|Não|
|Desligado|0|0/oculta|0/oculta|Não|

Tabela usa os overrides LedOpt1/2/4/6/7 instalados, parser em `0044...` do export anterior e consumo em `0041A250`. A tabela é indexada por modo-1, com modo0 usando índice6, stride0x40. +0 da entrada corresponde velocidade e +4 brilho; +0x10 habilita seleção de cor. O rótulo/valor de brilho foi confirmado no assembly0041A3BD..0041A3DE: +7C8→slider+758, +7C4→slider+1CFC. `0041AC20` grava modo+7C0, velocidade+7C4, brilho+7C8 e COLORREF+7CC. Cor em +7CC usa byte baixo vermelho, seguinte verde, seguinte azul; não tratar string hexadecimal do formato COLORREF como RGB web sem conversão. Efeito de logo usa +7F8/+7FC/+800/+804, condicionado a ShowLogoEffect; instalado0.

`0041A490` valida entradas decimais de cada canal e substitui valores acima255, selecionando o texto. `0041ACE0` aceita círculo de cor ou14 swatches, atualiza preview/modelo e aplica se ApplyNow. `0041A860` espera10ms e consulta gate de estado; só libera semáforo se a consulta falhar ou estado retornado0; caso contrário avisa. A dinâmica luminosa física permanece UNKNOWN.

### Dois tempos de repouso diferentes

`00409E80` preenche CAutoSleepDlg com1,2,3,6,12,18,24,30,36,42,48,54,60. O painter `00409A10` fecha a unidade: se valor<6, formata valor*10 com `%d s`; caso contrário (valor*10)/60 com `%d m`. Logo perfil+784 está em **dezenas de segundos**, e as opções são10s,20s,30s,1min,2min,...10min. `0040A210` limita índice a0..12 e grava o valor da tabela em +784; default6 significa60s. Não confundir índice, valor persistido e duração exibida.

O outro dropdown, perfil+770, usa SleepVal armazenado diretamente em segundos, com lista10,30,60,300,...2400 e default60 já documentada. Não mesclar os dois campos. A associação física exata entre sono do sensor, repouso do rádio e apagamento de luz requer correlação de firmware/readback; nomes de classe não resolvem isso.

### LOD e campo booleano +780

`00403420` pinta três rótulos LOD genéricos1/2/3mm, porém `00409240` grava +764 pela expressão2-(radio1!=0), e `00408840` só sincroniza1/2. Portanto o caminho UI/modelo examinado suporta efetivamente1 e2. Três rótulos de construção não estabelecem valor3 funcional. Valor3 no protocolo continua UNKNOWN até encontrar caminho independente/firmware.

Perfil+780 é booleano: refresh `00408840` transforma1/0 em radios+20C54/+20DC4; coleta `00409240` lê primeiro radio e grava0/1. Layout alternativo usa checkbox+19790 em `0043...`/`004396...`. Default1 confirmado em `0044DC00`. A associação nominal inequívoca a Motion Sync ainda não foi fechada: `tc_adv_str17`→globalD614 é pintado por0040399C, mas o encadeamento geométrico recuperado aqui não demonstra que seja o título desses radios. Não converter essa associação provável em fato. O texto D664 perto dos radios é **tc_sensor_tips**, confirmado loader004307E8/0043081D, e não nome da função. ShowMotionSync instalado0 continua sendo critério de visibilidade independente.

### Popups, erro e tray

Mensagem0x477 é um caminho explícito de cancelamento/fechamento: `0043E150` chama virtual+60, destrói via virtual+4(1) e zera popup global0060B374 quando popup existe e flag0060B36C=0. Cliques da janela e LED usam o mesmo padrão antes de prosseguir. Enquanto flag=1, esse caminho não destrói o popup; motivo completo da flag segue UNKNOWN.

`0043E250` fecha lacuna de tray: callback lParam0x202 (botão esquerdo solto) chama0043BD30; lParam0x205 (direito solto) traz último popup ativo ao foreground, cria menu com IDs6000/6001 separados por divisor, executa TrackPopupMenu, posta mensagem nula e destrói menu. Dispatch dos dois IDs confirmado no message map acima. Enter/Escape/Space/F1 consumidos em0043EAE0 não autorizam inferir apply/close automático.

`0042CA20` é wrapper genérico de diálogo customizado com texto recebido pelo chamador; a assinatura decompilada em chamadas com argumentos perdidos não permite atribuir uma única mensagem a todos os pontos de falha. As frases exatas por cada erro que ainda perde argumentos exigem assembly do chamador ou observação autorizada.

### Limites restantes, sem preenchimento por suposição

Resolvidos nesta rodada: handlers hotplug/behavior e seus bindings, agendamentos de descoberta/sync/bateria, supressão de notificação durante reset, readback seletivo de efeitos, valores discretos Windows, range LED versus defaults, campos LED centrais, unidade de +784, cancelamento0x477 e callbacks do tray.

Ainda UNKNOWN: geometria/renderização de todos os estados e diálagos raros em execução; resposta física, ACK/rollback, sono/reconexão real e firmware; associação nominal completa de +780; semântica da flag de popup; texto exato de cada chamada de erro com convenção não recuperada; suporte efetivo aLOD3; todas as indireções ainda não reconhecidas. Esses limites não são resolvidos por exportar mais uma vez as funções já reconhecidas. A nova descoberta de funções por message map é evidência concreta de por que a cobertura deve continuar delimitada.


## Descoberta HID

Fonte: private-analysis/OemDrv.exe.decompiled.txt, Cfg.ini instalado e levantamento preexistente runtime_hid_caps.json. Enderecos VA x86. Nenhum alvo executado, nenhum envio HID nesta tarefa. Assinaturas automaticas perdem argumentos em registradores/retornos: condicoes, offsets e chamadas concretas sustentam as conclusoes.

### Filtro e inventario

FUN_0044b7f0 carrega OPT/VID, PID, PID2 nas globais 0x005f781c/1e/20. Defaults compilados: VID25A7, PIDFA92, PID2FA99. Cfg.ini efetivo: VID25A7, PIDFA7B, PID2FA7C. OPT/NoMatchPID default0 controla 0x005f7824; ativo desabilita filtro VID/PID.

FUN_00411c80 chama HidD_GetHidGuid, SetupDiGetClassDevsW flags0x12 e SetupDiEnumDeviceInterfaces. FUN_00411d50 obtem DevicePath via SetupDiGetDeviceInterfaceDetailW, busca VID/PID ou VID/PID2 por StrStrIW e abre handle temporario. Acesso0x12019f (ou zero com 0x00605b14 ativo), share3, OPEN_EXISTING3. HidD_GetPreparsedData, HidD_GetAttributes, HidP_GetCaps fornecem atributos e capacidades. Fecha handle temporario.

FUN_00411c50 aloca slots de inventario 0x228 na tabela0x00605d08. Layout: path0x000..207; report-ID candidato208; Input len20c; Output len210; Feature len214; UsagePage218; Usage21c. FUN_00411f90 obtem report-ID candidato; filtros finais nao usam esse campo, usam comprimentos e usages.

FUN_0040d6c0 faz dois passes:

| Canal | UsagePage | Usage | Comprimento | CreateFileW final |
|---|---:|---:|---|---|
| Notificacao | FF01 | 0 | Input17 | acesso120089, share3, OPEN_EXISTING, OVERLAPPED40000000 |
| Comando | FF02 | 2 | Feature17 | acesso120116, share3, OPEN_EXISTING, flags0 |

### Pareamento e IO

FUN_0040d6c0 abre notificacoes primeiro e inicia FUN_0040d650: leitor FUN_00450700(payload15,timeout1000ms). Resposta valida publica handle em0x00605b10. Pass de comando zera global, envia por HidD_SetFeature **17 bytes: 08 03 e quinze zeros**, espera100ms e aceita somente com handle de notificacao publicado. Guarda os dois handles e paths, inicia FUN_0040d1d0.

Pareamento usa resposta ao probe, nao so coincidencia VID/PID ou texto de path. UNKNOWN: sincronizacao absoluta de0x00605b10 com respostas simultaneas; nao presumir associacao fisica perfeita com varios candidatos.

FUN_00450700 faz ReadFile17 OVERLAPPED, buffer iniciado por reportID9, espera evento, cancela IO em timeout e copia payload depois do primeiro byte. FUN_0044ffe0 e a thread continua: ReadFile17, evento IO e parada; erros48f desconexao e6 handle invalido; entrega buffer a FUN_0044fd50.

runtime_hid_caps.json preexistente confirma ambos FA7B/FA7C com FF01/0 Input17 reportID9 e FF02/2 Feature17 reportID8. FF04/2 Feature8 reportID6 e FF03/0 Input8 reportID2 tambem existem, alem de mouse/teclado/consumer/system padrao. **Os reports pequenos nao passam os filtros desse fluxo de configuracao.** Nao sao canais inutilizados pelo hardware/Windows em geral; ausencia de uso limita-se ao fluxo inspecionado. As chamadas HidD_SetFeature encontradas usam17 bytes.

### Prioridade com ambos PIDs

FUN_0040d1d0 verifica conexao por FUN_004503a0, consulta CID/MID por FUN_004504e0 e exige modelo suportado via FUN_0040d190. Esta busca pares CID/MID na tabela0x005f7954, registros0x6fc. Global bNotCheckPSD0x005f7704 ativa contorna identificacao e usa primeiro modelo; origem dessa configuracao UNKNOWN.

Apos HidD_GetAttributes, compara slots0x0060bc38 de tamanho0x440. **Para mesmo CID/MID**:

- Novo PID=OPT/PID, existente=OPT/PID2: sinaliza parada, fecha handles e zera slot anterior; aceita novo.
- Novo PID=OPT/PID2, existente=OPT/PID: log another dev has exist, give up this; fecha handles novos e desiste.

Cfg instalado implica **FA7B preferido a FA7C**, independentemente da ordem entre esses dois, condicionada a mesmo CID/MID reconhecido. Nao atribuir aqui cabo/receptor aos PIDs sem evidencia fisica propria. Para CID/MID distintos essa regra nao compara entre modelos: vencedor ativo pode depender da chegada/conclusao de threads. Dois dispositivos de mesmo PID: politica deterministica UNKNOWN.

Ao aceitar candidato, tambem sinaliza/fecha slot anteriormente ativo (campo+28), limpa marcadores de todos e marca novo ativo. Ha varios slots, mas uma selecao ativa. FUN_0040da80 limpa slots anteriores preservando o slot passado, sinaliza eventos e fecha handles. FUN_0040d1d0 le VersionNumber HID e publica PostMessageW0x7f5 para janela0x0060bbe0.

### Limites

Descoberta original emite probe HidD_SetFeature; reproduzi-la nao seria leitura estritamente passiva. Aqui foi apenas decompilada. Nenhum trafego capturado nem teste fisico de prioridade. Regras de prioridade sao evidencia estatica das comparacoes e fechamento de handles. Simultaneidade e timings nao foram exercitados. Detalhes de checksum/opcodes ficam na analise de protocolo.


## Protocolo de dispositivo

Evidência: OemDrv.exe SHA-256 `ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846`, Ghidra 12.2, VAs base 0x00400000. `private-analysis/protocol-assembly.txt` contém instruções conferidas, incluindo os pontos citados. Capacidades HID de dispositivos presentes em `runtime_hid_caps.json`. Este capítulo deriva do Ghidra; a segunda passagem DR03 corroborou22 consultas de leitura e suas respostas. Não houve captura de barramento USB; firmware e persistência após desligar permanecem UNKNOWN.

### USB-P01 — coleções e enquadramento

Ambos os PIDs configurados (FA7B e FA7C, VID25A7) têm as mesmas capacidades consultadas passivamente:

| UsagePage / Usage | Direção | Report ID | Comprimento incluindo ID |
|---|---|---|---:|
| FF02 / 2 | Feature | 8 | 17 |
| FF01 / 0 | Input | 9 | 17 |
| FF04 / 2 | Feature | 6 | 8 |
| FF03 / 0 | Input | 2 | 8 |

Fonte: `runtime_hid_caps.json`, 16 coleções no total, oito por PID. Não há OutputReport para essas coleções. O aplicativo investigado usa o par Feature8/Input9 nas rotinas abaixo; não foi estabelecido contrato funcional para os reports6/2. Não enviar o protocolo de17 bytes ao report6.

Feature8 tem 17 bytes: índice0=08; índices1…15=corpo do comando de15 bytes; índice16=checksum. `00450820` monta buffer zerado e envia `HidD_SetFeature(...,17)` em `004508C3`; caminho normal `004519F0`/`00451A06` também escreve ID08 (`00451A14`) e transmite17 bytes (`00451A56`…`00451A5A`).

**Checksum de envio:** com o byte16 inicialmente zero, definir byte16 como `(0x55 − soma(bytes0…15)) mod256`. A soma de todos os17 bytes será0x55 mod256. O algoritmo inclui o report ID08. Exceção: o probe de descoberta0040D6C0 transmite08 03 seguido de15 zeros, sem passar por este checksum; sua soma é0x0B, não0x55. Conferido nas instruções `00450890`…`004508BF` e `00451A23`…`00451A53`. No segundo caminho o algoritmo também lê o conteúdo anterior do byte16; chamadores o zeram antes de montar o comando. Não reutilizar um buffer com checksum antigo.

O wrapper `00450820` testa ponteiro nulo, embora a mensagem mencione tamanho maior que PER_PAYLOAD; não foi visto teste de tamanho nesse ponto. O clone deve impor tamanho de corpo15 e validar limites por conta própria. Isso é robustez proposta, não reprodução do comportamento inseguro.

### USB-P02 — envelope dos comandos e respostas

Definição de índices **P**: P0 é o comando (byte1 do report enviado); P15 é o checksum de resposta quando o ID já foi retirado. Não confundir P com offsets do frame bruto.

| Campo | Comando enviado | Resposta esperada no leitor |
|---|---|---|
| P0 | Comando | Mesmo comando para correlação |
| P1 | Normalmente0 | Status;0 é sucesso nos consumidores examinados |
| P2/P3 | Endereço alto/baixo quando aplicável | Cabeçalho devolvido; sem validação geral demonstrada |
| P4 | Comprimento quando aplicável | Campo de envelope |
| P5…P14 | Dados, até10 bytes | Dados retornados, até10 bytes |
| P15 | Fora do corpo15; checksum fica no frame16 | Último byte copiado pelo leitor; validação de checksum recebido não encontrada nas rotinas examinadas |

EEPROM usa endereço16 bits **big-endian**, embora arquivos/estruturas do host sejam little-endian. Escrita `00450EA0`…`00450EAD` monta P0=07,P1=0,P2=addr>>8,P3=addr,P4=len,P5…=dados. Leitura `004511AC`…`004511C6` monta P0=08,P2=addr>>8,P3=addr,P4=len. Não confundir ID08 com comando08.

### USB-P03 — catálogo de comandos encontrados

| Cmd P0 | Entrada/saída e estado | Evidência e limite |
|---|---|---|
| 01 | Identificação/check de modelo: P4=08, P5…P8 quatro números pseudoaleatórios1…100, P9/P10 zerados na consulta. Consome resposta status0 e CID em P9/MID em P10. | `004504E0`, montagem `00450538`…`0045057B`; diagnóstico CheckPsd. Função gera números com rand sem prova de autenticação criptográfica; transformação/validação do desafio UNKNOWN. |
| 02 | Comando genérico especial com P4=1 e argumento em P5. | `00450910`, ramo de cmd2. DR02 confirma P5=1 ao mostrar e P5=0 ao ocultar o aplicativo, com ACK real. Isso é status do driver; não inferir factory reset do número02. |
| 03 | Consulta de conexão; consulta inicial lê Input9 diretamente com timeout200ms e até3 respostas de comando divergente. Status0 produz conexão aceita. | `004503A0`; consulta posterior `00450AB0`/`00450BB0`. Valores de status não zero não têm enumeração semântica confirmada. |
| 04 | Consulta dois valores, consumidos como energia e carregamento pelo fluxo superior. | `004518E0`; dados P5,P6; chamada de UI e strings GetPower. Escala física, flags completas e erro do sensor UNKNOWN. |
| 07 | Escrever EEPROM, até10 bytes por transação padrão, esperar ACK comando07/status0. | `00450DC0`; addr/len/data acima. Há parâmetro de chunk alternativo; tamanho máximo seguro efetivo não demonstrado além do corpo15. |
| 08 | Ler EEPROM, até10 bytes por transação; esperar cmd08/status0 e copiar dados P5… conforme tamanho solicitado. | `00451120`, cópia após status em `00451214`…; `00451080` itera chunks≤10 com5ms entre eles. |
| 0A | Notificação espontânea, separada da fila de ACK. | `0044FD50`, bits descritos abaixo. |
| 0E | Consultar perfil atual. | `00450B40` chama consulta genérica `00450BB0(0x0E,...)`. Indexação e quantidade dependem do modelo. |
| 0F | Consulta de estado, resultado lógico deriva de P5==0. | `004517E0`; significado físico completo UNKNOWN. |
| 10 | Selecionar perfil: P4=1,P5=índice8 bits, espera cmd10. | `00450CE0`; fluxo superior registra SetCurProfile. Não é prova de quatro bancos de EEPROM completos. |

`00450910` também envia comandos genéricos escolhidos pelo chamador. Eventos de abrir/fechar interface passam estado1/0 por `0043BD30`/`0043BDA0`; a recuperação de convenção de chamada é imperfeita. Não atribuir a todo comando genérico a mesma semântica de status do driver.

### USB-P04 — máquina de transporte, concorrência e falhas

1. Descobrir par de handles de comando/notificação e identificar CID/MID. A seleção detalhada é registrada no capítulo de descoberta.
2. Inicialmente consulta03 e identificação01 leem diretamente Input9 com timeout200ms (`004503A0`, `004504E0`, `00450700`). `00450700` usa leitura overlapped e cancela I/O quando expira.
3. Após seleção, `0040D1D0` cria evento/thread `0044FFE0`. Thread mantém ReadFile17 bytes com report9, espera evento de leitura ou parada. Para o dispatcher, passa ponteiro após o ID; confirmar pelos callsites exportados de `0044FFE0`.
4. Dispatcher `0044FD50` envia notificações0A à interface e enfileira outras respostas de16 bytes. `0044FEE0` correlaciona **somente o comando P0**, descartando respostas diferentes enquanto procura a esperada. Não há transaction ID observado.
5. Chamadores serializam operações com objeto de lock em `device+0x440`, limpam fila (`00451BB0`), enviam, aguardam resposta e soltam lock. O clone precisa evitar dois comandos iguais em voo e respostas antigas; escolha de projeto baseada nesse mecanismo.
6. Espera de fila começa com10ms, faz polls com20ms e contador>50 para timeout (`0044FEE0`); aproximadamente1s quando a fila fica vazia. Respostas divergentes podem prolongar esse limite: o contador só avança no caminho de fila vazia.
7. Envio normal tenta SetFeature até3 vezes e dorme50ms após falha (`00451A44`…`00451A6A`). O envio inicial `00450820` não contém essas três tentativas. Retries de ACK vêm de `DAT_005F78A8`, configurado pela opção Retry; não misturar os dois níveis.
8. ReadFile erro0x3E5 é operação pendente;0x48F ou6 encerra thread; sinal de parada cancela leitura e fecha evento (`0044FFE0`). Isso mapeia a erro de remoção/handle inválido em Windows; errno Linux exige tradução própria.

ACK com P1!=0 ou timeout falha/retry nos leitores examinados. Alguns caminhos de escrita continuam após esgotar tentativas; por exemplo `00450DC0` avança chunks mesmo sem ACK válido em certos ramos e pode finalizar com sucesso. O clone não deve comunicar sucesso confirmado sem seu próprio critério de confirmação; replicar essa falha é uma decisão de compatibilidade, não requisito de funcionalidade.

### USB-P05 — notificações0A

Dispatcher examina P5 como máscara, e publica mensagem interna0x7EB com subtipo:

| Bit P5 | Valor consumido | Subtipo de UI |
|---|---|---:|
| 0x01 | P6 | 1 |
| 0x02 | P7 &0x0F | 2 |
| 0x04 | P9 | 3 |
| 0x80 | Nenhum | 4 |
| 0x40 | Nenhum | 5 |
| 0x20 | Nenhum | 6 |

Evidência `0044FDD0`…`0044FE6F`. Mapeamento dos subtipos para DPI/perfil/iluminação/reset exige fluxo superior `0043Exxx`; campos não usados e bits0x08/0x10: UNKNOWN. A tabela é contrato de despacho estático, não captura de evento real.

### USB-P06 — mapa EEPROM observado

Offsets são de **EEPROM do protocolo**, não do arquivo DCT. Base e capacidade física completa: UNKNOWN. `0040F660` lê bloco inicial e nomes/combinações; `00410EE0` escreve recursos por máscara. Cada campo abaixo tem evidência em uma dessas funções ou codecs indicados.

| Offset/range | Conteúdo e codificação |
|---|---|
| 0000…0001 | Polling: byte valor + complemento `0x55−valor`. Codificador `00451780`: app0x1000→1,0x500→2,0x250→4,0x125→8. Leitor0040F660 faz inverso. UI00403420 confirma125/250/500/1000Hz. |
| 0002…0003 | Quantidade de estágios DPI + complemento. `00410EE0` máscara0x80. |
| 0004…0005 | Estágio DPI atual + complemento. `00410EE0` máscara0x10. |
| 000A…000B | LOD + complemento. `00410EE0` máscara0x200; leitura local590+0xA em0040F660. Valores permitidos/unidade não fechados aqui. |
| 000C…002B | Até8 estágios ×4 bytes: Xbaixo,Ybaixo,controle,checksum de registro. `004513B0` escreve; `0040F660` lê. |
| 002C…004B | Até8 cores ×4 bytes: três componentes e `0x55−soma3`. `00451290`. Ordem literal é byte baixo, seguinte, seguinte do campo de cor; nomes RGB/BGR dependem do modelo lógico. |
| 004C…0053 | Parâmetros do efeito DPI,8 bytes. Leitor nomeia DPI Effect, escritor00410EE0. Contrato completo dos índices/tabelas de velocidade UNKNOWN. |
| 0054…005D | Efeito secundário/logo; escrita condicional em00410EE0, flags do modelo. Não prova que esteja habilitado no AJ199. |
| 0060…009F | Matriz16 posições ×4 bytes: ação24 bits little-endian e complemento0x55−soma3. `00451640`; não equivale a16 botões físicos. |
| 00A0…00A6 | Sete bytes de parâmetros da iluminação principal; codificador00410EE0. Mapeamento completo de efeito/brilho/cores UNKNOWN nesta camada. |
| 00A9…00AA | Debounce8 bits + complemento. `00410EE0` máscara0x1000 e0040F660. Unidade ms apoiada pela UI. |
| 00AB…00AC | Chave de iluminação/estado lógico + complemento; leitor normaliza byte para boolean. `00410EE0` máscara0x2000 e0040F660. |
| 00AD…00AE | Tempo de economia dividido por10 para envio; leitura multiplica por10. `00410EE0` máscara0x4000 e0040F660. Unidade UI confirmada em segundos por00419D00/004197E0. |
| 00AF…00B0 | Correção de linha/ângulo (FixLine) + complemento. `00410EE0` máscara0x400 e0040F660. |
| 00B1…00B2 | Ripple + complemento. `00410EE0` máscara0x800 e0040F660. |
| 00B3…00B4 | Apagar luz ao mover + complemento. `00410EE0` máscara0x10000 e0040F660. |
| 00B5…00B6 | Auto-sleep: perfil+784, unidade host10 segundos, máscara0x40000; segunda passagem confirmou mapa e UI. Valor lidoFF não confirma suporte físico. |
| 00B7…00B8 | Opção booleana de sensor: perfil+780, máscara0x20000; nome Motion Sync ainda candidato. Valor lidoFF não confirma suporte físico. |
| 0100…02FF |16 slots ×32 bytes para combinações; leituras no0040F660, codec0040EEA0. Somente20 bytes por slot lidos no caminho examinado. |
| 0300 + i×0180 | Área macro por posição de matriz,16 slots. Nomes lidos de0301…031E, contagem em031F e primeiro evento em0320; codec de macro detalhado no capítulo de macros. |

Registros simples de parâmetros usam checksum somando0x55, além do checksum do frame17. O checksum de macro é calculado antes de preencher a área de nome e portanto exclui essa área; ver capítulo de macros. Não atribuir esse checksum a todo arquivo .jma/.jmm: são formatos distintos.

### USB-P07 — DPI PAW3395 e discrepância do escritor

`0040CA40`: para sensor0x3395 e DPI<0x65F4 (26100), código=`DPI/50−1`, multiplicador0. `0040CE10` decodifica `(código+1)×50` quando bit0 do multiplicador é0, e×100 quando é1. UI instalada limita50…26000 em passos50 (confirmar capítulo de UI).

Leitor0040F660 recupera código X=`b0 | ((b2&0x0C)<<6)`, código Y=`b1 | ((b2&0xC0)<<2)`; multiplicador X=`b2&3`,Y=`(b2>>4)&3`; b3 é checksum. Portanto formato lógico inverso coloca bits altos de X nos bits2/3 e de Y nos bits6/7.

**Discrepância real entre escrita individual e em lote:** assembly `0045147F`…`004514AA` do ramo máscara0xFF não desloca o nibble alto de X por2, e usa o indicador de multiplicação X também para Y. Ramo individual em004515xx desloca os bits altos X. Não foi executado teste de DPI alto/XY para determinar impacto no firmware. Especificação deve preservar essa divergência como **UNKNOWN de equivalência**, em vez de afirmar um único algoritmo de envio já validado. Implementação Linux proposta: modelar o formato pelo leitor/inversão e validar com captura/roundtrip antes de habilitar escrita geral. Não reproduzir automaticamente um possível defeito do fornecedor.

### USB-P08 — ações24 bits conhecidas

Codec de ida `004103E0` e volta `0040F1C0`:

| Ação lógica | Valor24 bits na matriz |
|---|---|
| Esquerdo/direito/meio/voltar/avançar | 000101 /000201 /000401 /001001 /000801 |
| Duplo clique esquerdo / três cliques |023204 /033204. Internos01:16/17, loader00431BC5 e00432A56, menu00414EC0; o rótulo de duplo clique direito não confirma um codec distinto. |
| Desativado |000000 |
| Combinação/teclado/mídia |000005, dados auxiliares no slot de combinação |
| Macro contada |`(ciclos8bits<<16)|(índice_matriz<<8)|000006` |
| Macro até soltar |FE0006 acrescido do índice de matriz no byte médio |
| Macro modo alternado |FF0006 acrescido do índice de matriz no byte médio; rótulo “até qualquer tecla” não comprova mecanismo físico completo |
| DPI + / − / ciclo |000202 /000302 /000102. Correlação loader00432903/00432974/004329E5 → globalsD560/D564/D568 → menu00414EC0 → especiaisA8/A9/AA → codec004103E0. |
| Alternar polling / luz on-off / perfil |000007 /000008 /000009; loader00432DDE/00432BA9/00432FA2, menu e codec004103E0. |
| Bloqueio de DPI |Tipo baixo0A, argumento/código DPI no byte seguinte; interno08:A6, loader00432C1A. Codificação DPI3395 completa com bits altos permanece UNKNOWN para este caminho especial. |

Macro contada armazena somente byte baixo da contagem no código de ação, apesar de o arquivo conter uint16; UI limita1…250. Máscara de teclas e mapeamento de botões físicos condicionam posições válidas. Não enviar matriz inteira com posições não confirmadas só porque o formato comporta16.

### Vetores de montagem derivados, não capturados

Para teste unitário independente do codec, sem afirmar resposta real:

- Ler EEPROM endereço0000,10 bytes: `08 08 00 00 00 0A 00 00 00 00 00 00 00 00 00 00 3B`.
- Consultar perfil atual cmd0E: `08 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 3F`.

Estes vetores resultam do envelope/checksum estático, não foram transmitidos. Vetores de resposta foram obtidos na segunda passagem DR02/DR03; os exemplos deste capítulo foram originalmente derivados e depois corroborados para leitura. Endpoints USB físicos, intervalos de polling USB, tráfego de rádio, firmware interno e protocolo bootloader: UNKNOWN.


## Codec detalhado e discrepâncias confirmadas no host

Alvo: OemDrv.exe SHA-256 `ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846`, PE x86, base VA00400000. Evidência primária: export integral Ghidra12.2 `private-analysis/OemDrv.exe.decompiled.txt`, instruções em `private-analysis/protocol-assembly.txt` e `private-analysis/ui-targeted-assembly.txt`, complemento assembly `private-analysis/deep-ui-recovered.txt`, bytes do PE privado `inputs/OemDrv.exe`, mapa de seções `OemDrv.exe.pe.json`. Esta revisão reutiliza a análise Ghidra existente conforme o workflow REA; não abriu outro projeto, não executou OemDrv, não enviou reports e não observou firmware. VAs de funções indicam análise do corpo completo; VAs de instruções são usadas onde há export assembly conferido. Decompilação com convenções de chamada incorretas não estabelece por si só tamanho de transferência.

### DP01 — divergência DPI é fechada no host, não no firmware

Para PAW3395 no intervalo configurado50..26000, `0040CA40` retorna C=DPI/50−1 e multiplicador M=0. Definir Hx=(Cx>>8)&15, Hy=(Cy>>8)&15. As duas rotas de `004513B0` gravam Xbaixo,Ybaixo,controle,`55−soma3`:

| Rota | Controle PAW3395 |
|---|---|
| máscaraFF, lote | `(Hx | (Mx!=0)) | (((Hy<<2) | (Mx!=0))<<4)` truncado a8bits |
| máscara diferente deFF | `((Hx<<2) | (Mx!=0)) | (((Hy<<2) | (Mx!=0))<<4)` truncado a8bits |

Assembly lote `0045147F..004514AA` comprova ausência dos dois ADD que deslocariam Hx. Individual `004515C7..004515F1` contém esses ADD em `004515D3/004515D5`. **Ambas** usam o multiplicador X para Y: lote compara a mesma pilha+18 em `00451487/0045149D`; individual testa o mesmo ESI em `004515D7/004515EA`, ignorando o multiplicador Y calculado. No intervalo instalado Mx=My=0; portanto este segundo defeito não altera esse intervalo, mas permanece real para combinações que escolhem multiplicadores distintos fora dele.

Leitor `0040F660` reconstrói Cx=b0|((b2&0C)<<6), Cy=b1|((b2&C0)<<2), Mx=b2&3, My=(b2>>4)&3 e chama `0040CE10`. Este decoder testa o bit0 do multiplicador para50/100. Consequência estática verificável, **sem enviar ao dispositivo**:

| DPI X=Y | C | Registro lote | Registro individual | X reconstruído pelo leitor do lote |
|---:|---:|---|---|---:|
|12850|0100|00 00 41 14|00 00 44 11|100|
|26000|0207|07 07 82 C5|07 07 88 BF|400|

Para DPI<=12800, Hx=0 e a divergência de Hx não aparece. Não há base para tratar as duas rotas como equivalentes. O que permanece UNKNOWN é a interpretação efetiva pelo firmware e a frequência com que UI/import invocam cada rota; o binário prova os bytes diferentes.

Outro limite: máscara nãoFF procura bits0..7 em ordem crescente e **retorna após a primeira escrita**; não é escrita de todos os bits ligados. `00451550..0045157B`, chamada `00451626` e epílogo subsequente. O lote envia N×4 bytes desde EEPROM000C, chunk alternativo8 na chamada `00451525/0045152A`. O banco lógico tem8 registros, mas N deve ser validado externamente antes de reproduzir esse caminho.

### DP02 — checksum de frame inclui exatamente17 bytes anteriores à substituição

`00450820` soma offsets0..15 em pares (`00450890..004508A2`) e lê offset16 separadamente (`004508A9`), depois sobrescreve16 (`004508BF`). Seu buffer é zerado antes da cópia (`00450854..00450860`) e ID08 é preenchido em `00450875`; portanto com corpo de15 bytes o byte16 anterior é0. A fórmula habitual é `frame[16]=(55−sum(frame[0:16]))&FF`.

`004519F0/00451A06` faz a mesma soma completa: ESI=EDI+1 (`00451A0A`), acessos ESI+EAX−1 e ESI+EAX somam offsets0..15 (`00451A23/27`), e `00451A3B` lê EDI+16. Em seguida `00451A53` sobrescreve16. Fórmula exata desta implementação é `novo16=(55−sum(antigo[0:17]))&FF`. Assim, um checksum anterior nãozero é subtraído novamente. Os chamadores de EEPROM explicitamente zeram os16 bytes após o primeiro byte antes de cada envio, por exemplo `00450FC6..00450FD2`, logo o uso normal produz a fórmula habitual. Não há leitura de offset17 no checksum.

A cópia usa o comprimento fornecido pelo chamador; `0045082E` testa ponteiro nulo e não comprimento. Corpo15 é limite do formato observado, não uma validação de segurança demonstrada no wrapper. A resposta recebida não ganhou validação de checksum por esta revisão: continua UNKNOWN fora dos consumidores examinados.

### DP03 — bloqueio DPI perde bits altos explicitamente

`004103E0`, classe08/minorA6: resolve valor lógico por `0040D070`, chama `0040CA40` com ponteiro de multiplicador nulo, e retorna `((C&FF)<<8)|0A`. Assembly `0041048B..004104B7`, sobretudo MOVZX EAX,AL em `004104AB`, confirma a truncagem. Não há lugar preservado para C alto nem multiplicador nesse retorno; o byte superior da ação24bits fica0. Isto fecha a lacuna da codificação host: ela **trunca**, em vez de transportar todos os bits do DPI3395.

Para valores50..12800 C cabe8bits. Valores12850..26000 colidem por módulo256 (ex.:12850 e50 produzem00000A;26000 e400 produzem00070A). Isto não comprova DPI físico efetivo nem ausência de interpretação especial no firmware. Inversor `0040F1C0` confirma a perda: `0040F3CD` desloca ação por8; `0040F3D0` extrai apenas DL em EAX; `0040F3D3` zera EBX (multiplicador); `0040F3DD` chama `0040CE10`. Para3395 isto decodifica `(byte+1)×50`. Depois `0040F3E2..0040F3ED` resolve índice lógico por sensor via `0040D010`. Os exemplos de colisão acima são portanto reproduzidos pelo próprio leitor do aplicativo.

### DP04 — correção necessária: B5 e B7 não seguem a ordem dos campos de perfil

No escritor `00410EE0`:

| Perfil | Máscara | EEPROM valor/checksum | Interpretação apoiada |
|---|---:|---|---|
|+780|20000|00B7/00B8|boolean de opção de sensor; candidato Motion Sync |
|+784|40000|00B5/00B6|auto-sleep, seleção da CAutoSleepDlg |

Cada par grava byte baixo e55−byte. Assembly recuperado confirma os argumentos: `00411AD5` lê+780 e `00411AE8` selecionaB7; call `00411AF7`. `00411B19` lê+784 e `00411B2C` selecionaB5; call `00411B3B`. Leitor `0040F660` mantém correspondência: EEPROM B5 vai para global0060BB0C, B7 para0060BB08; os offsets desses globais relativos ao perfil temporário0060B388 são784 e780.

Nome de auto-sleep tem evidência adicional independente: RTTI/vftable CAutoSleepDlg em `00409860/00409870/00409930`; `00409E80` inicializa tabela de13 valores `[1,2,3,6,12,18,24,30,36,42,48,54,60]`; `0040A210` escreve o item selecionado em perfil+784 e publica máscara40000. `00414160` também copia esse item para+784. Default+784=6 em `0044DC00`. Painter00409A10 confirmou unidade host de10 segundos para+784: valor6 significa60s. Sua interpretação física no firmware permanece UNKNOWN. Não confundir com perfil+770/EEPROM AD.

Perfil+780 é atualizado como boolean em `00409240`, a partir do primeiro radio da dupla UI+20C54/+20DC4; `00408xxx` o apresenta como pares1/0. A ligação nominal exata dessa dupla à chave ShowMotionSync necessita confirmação de UI/handlers. **A tabela anterior que atribuía B5 ao candidato Motion Sync e B7 ao candidato auto-sleep deve ser invertida**, mesmo antes de fechar o nome Motion Sync.

### DP05 — parâmetros LED recuperados como codec, sem nomes inventados de efeitos

`00410EE0` e inversor `00410050` fecham o layout significativo do efeito principal EEPROM A0:

`[modo_wire, cor_byte0, cor_byte1, cor_byte2, velocidade_wire, brilho_wire, checksum]`

O checksum de registro soma os seis primeiros bytes com o sétimo para55. A cor é os24bits baixos de perfil+7CC, little-endian; COLORREF de UI usa byte baixo vermelho, seguinte verde, seguinte azul, conforme0041AC20/0041A490. A luz física não foi comparada visualmente. Perfil+7C0=modo lógico; +7C4=índice de velocidade; +7C8=índice de brilho. Nomes humanos dos modos não são deduzidos desta numeração.

| Modo lógico | Modo wire | Tabela velocidade | Tabela brilho |
|---:|---:|---|---|
|0|4|preserva bytes existentes via leitura|preserva bytes existentes via leitura|
|1|2|005DD59B|005DD5A7|
|2|1|005DD59B|005DD5A7|
|3|0|005DD58F|005DD583|
|4|3|005DD59B|005DD5A7|
|5|5|005DD59B|005DD5A7|
|6|7|005DD59B|005DD5A7|

O inversor `00410050` trata wire2 como lógico1 e pesquisa apenas brilho, devolvendo velocidade1; logo o leitor não preserva a velocidade enviada por esse modo. Valores não encontrados nas tabelas têm fallback/diagnóstico, não validação geral de faixa no escritor.

Modo lógico0 não envia uma cor nova zerada: lê os7 bytes existentes, troca só modo por4 e recalcula checksum. Portanto um cliente que pretende preservar o comportamento precisa read-modify-write para este ramo. Transferência é exatamente7 bytes: `004114DE` põe EDX=7 antes do call `004114E8`; ramo modo0 também usa7 em `0041145C`. Portanto A7 não é escrito por este codec.

Tabelas literais do PE, índices0..10 (o zero inicial é índice0, os leitores procuram índices1..10 e devolvem1-based):

| VA | Bytes hex0..10 |
|---|---|
|005DD577|00 10 1E 3C 5A 80 96 B4 D2 E6 FF|
|005DD583|00 48 5C 70 84 98 AC C0 D4 E8 FC|
|005DD58F|00 0A 09 08 07 06 05 04 03 02 01|
|005DD59B|00 FF E6 D2 BE AA 96 82 6E 46 28|
|005DD5A7|00 2D 32 4B 64 7D 96 AF C8 E1 FF|

Extração sem executar: seção.data, valores canônicos do JSON: RVA1929216, raw1923584; offset de arquivo=VA−400000−1929216+1923584. Os VAs e bytes acima foram conferidos diretamente no arquivo.

EEPROM4C efeito DPI tem pares independentes no buffer local: `[perfil788,55−perfil788,T577[perfil790],55−T577[perfil790],perfil78C,55−perfil78C,0,0]` para modo nãozero. Quando modo0 o buffer permanece `[0,55,0,0,0,0,0,0]`. Leitor `0040F660` lê modo em4C, busca velocidade de4E na tabela577 e lê parâmetro em50 diretamente; nomes físicos de78C/790 ainda dependem UI. Isto é checksum por par. **Transferência real é2 bytes no modo0** (`00411555` EDX=2), **6 bytes nos outros modos** (`00411598` EDX=6), call `004115A7`. Os dois zeros finais do buffer não são enviados. Assim4C..53 é área lida, mas escrita deste codec só altera4C..4D ou4C..51.

Efeito logo EEPROM54: três bytes de cor(+804), checksum da cor em57; modo(+7F8) em58 e complemento59; velocidade T5A7[+800] em5A e complemento5B; parâmetro+7FC e complemento em5C/5D. O ramo modo0 altera somente par58/59. Transferência exatamente10 bytes confirma54..5D: `0041169A` EDX=0A, call `004116AB`; ramo modo0 exatamente2bytes em58/59 (`0041161E` EDX=2, call `00411621`). Habilitação por modelo+620, não demonstra suporte AJ199.

### DP06 — capacidade e checksums de macro/combinação

Inicialização `0044CE00` define capacidade de bytes0060BBF4=180h, slots0060BBF8=16, eventos0060BC04=46h=70 e atraso0060BC00=FFFFh. `00410BB0` zera384bytes, inicia comprimento L=32 e acrescenta5 por evento; para antes de ultrapassar capacidade e limita explicitamente70 eventos. N=70 ocupa L=382, checksum em382, byte383 permanece0. Não cabe um71º evento no slot384. Estes são limites host concretos desta inicialização, não capacidade física total do firmware.

`00410EE0` calcula checksum em buffer ainda com bytes0..30 zerados; byte31=N já foi preenchido. Depois copia nome (máx15 unidades UTF16LE) e comprimento2×unidades. Portanto checksum de macro final equivale a `55−sum(bytes[31:L])`, com L=32+5N, independente do nome. Checksum em L; o nome final não participa. Para N<=69, o chamador escreve zeros L+1,L+2,L+3; para70 não faz esses três writes. **Comprimento realmente enviado é L+4 para N<=69, e L+1=383 para N=70**: `00411062` guarda L em EDI, `004110B0` incrementa para L+1, `004110BA` compara com17Dh, `004110C2..004110DA` zera três bytes e soma3 somente no ramo menor, e `0041115F` passa EDX=EDI à escrita `004111F8`. O byte final383 do slot máximo é inicializado no buffer mas não enviado. A combinação usa EDX=payload+1 em `004111EF` e chunk10 em `004111F3`; macro usa chunk0 em `0041115D` para o default do escritor. Leitura do firmware validar ou ignorar isto permanece UNKNOWN.

Combinação: se m modificadores ativos (0..4) e k teclas nãozero (0..3), `00410680` gera2(m+k) registros de3bytes e byte de quantidade, logo comprimento antes de checksum `1+6(m+k)`. Depois checksum, ocupação=`2+6(m+k)`; para caber em slot32 exige m+k<=5. Os casos6 e7 ocupam38 e44bytes e ultrapassam o slot. Não foi demonstrada trava UI suficiente nem truncamento seguro; essa combinação de parâmetros precisa rejeição explícita em um cliente independente. Leitura de combinações `0040F660` busca somente20bytes por slot, o que cobre integralmente no máximo3 pressionamentos mais3 solturas; no entanto `0040EEA0` para no primeiro release e pode recuperar apenas prefixo de pressões em casos maiores. Não promover roundtrip universal.

### DP07 — roda e duplo clique direito: limites negativos precisos

Em `004103E0`, classe01 só tem casos11..17:11/12/13/14/15 botões,16 duplo esquerdo,17 triplo. Não há caso de roda nem duplo direito nesse switch; valor não reconhecido retornaFFFFFFFF. Os especiais incluemA4 como ação configurável tipo4 (`argumento+10/+11` reorganizado), mas não foi estabelecido que a UI de duplo direito usaA4; preservar esta possibilidade como UNKNOWN em vez de dizer impossível no firmware.

`00410BB0` só possui mouseF0..F4; F5/F6 caem na busca de104 pares HID/VK. Esses pares não contêm VKF5/F6 (valores hexF5/F6, não as teclas de função F5/F6 cujo VK é74/75); logo o caminho emite código0 com diagnóstico, em família de tecla, em vez de um evento de roda definido. `00410910` também não possui inverso de roda entre eventos mouse. Isto fecha ausência de codec de roda **nestas duas rotas**, não ausência global de suporte no firmware ou de outra funcionalidade não localizada.

### Limites restantes

A segunda passagem DR03 obteve22 pares de leitura/ACK reais e185 bytes da EEPROM; ver capítulo runtime. Persistência após reiniciar, escrita de ajustes, comportamento físico para DPI divergente/truncado, semântica física de auto-sleep B5, nome final do boolean B7 e limites físicos da EEPROM permanecem UNKNOWN. A unidade host de B5 foi fechada pela UI; validar checksum RX no clone é escolha proposta, não comportamento do original demonstrado. Os vetores DPI, checksums, limites de combinação e comprimentos de macro desta revisão foram recalculados por aritmética independente (sem protocolo/hardware). Não implementar escritas com base em suposta equivalência de duas rotas ou em tamanho inferido de protótipo decompilado. Correções propostas de cliente independente devem ser identificadas como escolhas de implementação e validadas separadamente contra hardware autorizado.


## Observação e consultas reais REA/Frida

Segunda passagem, 24/10/2026. Diferentemente da primeira passagem passiva, esta sessão instrumentou o OemDrv **já em execução**, mostrou sua janela, percorreu as quatro páginas e enviou consultas explícitas de leitura ao dispositivo. Não iniciou instalador/desinstalador, não reiniciou o driver, não enviou comando07 de escrita EEPROM nem reset/firmware, e não alterou intencionalmente parâmetros físicos. Ao terminar, a janela foi ocultada novamente pelo botão de minimizar do original.

### DR01 — ferramenta, identidade e evidências

REA6.7.0 CLI `instrument-with-frida attach 5112`, scripts locais identificados por SHA-256 dentro de cada Evidence. O binding nativo opcional do Frida17.23.2 estava ausente no cache npm; foi obtido pelo `prebuild-install` do pacote existente, sem mudar registro MCP, configurações do Codex ou Ghidra. Todas as capturas concluídas têm `cleanup_error=null`; attach/detach não implica iniciar/parar o processo alvo.

| Arquivo | REA Evidence ID | Alcance |
|---|---|---|
|rea-frida-identity.json|ev_387734a0805a9b6bef82be7684796a59a7a65b306d874af2d217db19edfeda2c|PID, arquitetura e módulos carregados|
|rea-runtime-show.json|ev_b9dcdb73c23185ee05f6c7a4d6ed9f9f0706eb07cb9475057053cdd0d94ccfb3|Hooks de API e dispatcher ao mostrar janela|
|rea-runtime-navigation.json|ev_9b763b0f0b33810114d37c28188264571d69f4a73e078c7d6d1325ae15598d96|Navegação dos quatro botões sem selecionar ajustes|
|rea-device-readback.json|ev_4bf2e6c2bd35285c94d8c0ad5d9b3e1244744655e191e7273a0a973e541535b4|22 consultas explícitas e22 respostas|
|rea-runtime-state-snapshot.json|ev_9cc5c5862df698bee70ae106084da74bf6172c006a45bfe12a8ea32490e2847d|Globals de configuração, modelo e perfil na memória do processo|
|rea-runtime-restore-hidden.json|ev_06730d1ba3968a148ef6cea419fe7f484c06887f54ee81a368cc32210ed30501|Minimizar/ocultar pelo original; status0 e ACK|

O provider REA reporta sua limitação de identidade de artefato e SO. A vinculação adicional desta investigação é explícita: PID5112, `Process.arch=ia32`, caminho instalado OemDrv.exe e base runtime00800000. Três amostras de16 bytes nas VAs estáticas00450820,0044FD50,00451120 foram comparadas com o PE de hash ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846, aplicando as relocations HIGHLOW do próprio PE para delta00400000: as três conferem. Isso vincula amostras concretas; não é comparação integral de toda a memória carregada. `analyze_runtime_readback.py` e `runtime-readback-summary.json` reproduzem essas verificações.

O usuário informou **somente cabo USB**. O handle consultado respondeu HidD_GetAttributes com VID25A7/PIDFA7B/VersionNumber0341. Assim FA7B está confirmado como o canal respondente nesta situação relatada; a informação não demonstra universalmente a topologia física dos dois PIDs. VersionNumber é atributo HID, não uma versão semântica de firmware já decodificada.

### DR02 — tráfego observado do original

Ao mostrar a janela por mensagem0x46C/lParam202, a chamada original em00451A5F enviou:

`08 02 00 00 00 01 01 00 00 00 00 00 00 00 00 00 49`

Resposta no dispatcher0044FD50, já sem o ID de entrada:

`02 00 00 00 01 01 00 00 00 00 00 00 00 00 00 48`

Isso confirma cmd02 com comprimento1/valor1 no fluxo de mostrar/status do driver; não é comando de factory reset por esse uso. Hooks registraram API retornando1. Há também consultas03 periódicas de outro handle durante a janela observada; ausência de resposta no dispatcher não estabelece falha desse outro dispositivo, pois a fase de descoberta tem leitor direto separado.

Ao restaurar a janela para oculta, o original enviou `08 02 00 00 00 01 00 00 00 00 00 00 00 00 00 00 4A` e recebeu corpo `02 00 00 00 01 00 00 00 00 00 00 00 00 00 00 49` (seq25/26 da Evidence de restauração). EnumWindows confirmou a mesma janela133020 invisível, mantendo o mesmo PID5112. Não houve fechamento/reinício do driver.

Consulta periódica de bateria original:

TX: `08 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 49`

RX corpo: `04 00 00 00 02 64 00 00 00 00 00 00 00 00 00 E2`

Interpretação corroborada por004518E0: comprimento2, percentual100, carregando0. O indicador visual mostrou100%. Isso é resposta real e interpretação do host; não certifica precisão eletroquímica da medição.

### DR03 — consultas controladas de leitura

`read-device-probe.js` verificou primeiro os atributos do handle e usou somente comandos03,08,0E e0F. O comando08 faz **leitura EEPROM**, apesar de o transporte HID usar uma chamada SetFeature para enviar a solicitação. O comando07 de escrita não foi usado.

Houve22 solicitações com API_result1 e22 respostas correlacionadas: consulta de perfil, conexão, estado0F e19 chunks cobrindo exatamente **185 bytes, endereços0000…00B8**. Todos os comandos/ACKs, status0, endereços, comprimentos e checksums conferem no verificador independente. Nenhuma resposta desse conjunto está faltando ou truncada. O verificador não amplia a cobertura a outras regiões ou operações.

O checksum dos17 bytes de solicitação soma55h módulo256. As respostas capturadas no dispatcher têm16 bytes sem ID; acrescentar o ID09 declarado pelo leitor/capacidades faz todas somarem55h. Essa observação corrobora o checksum, sem afirmar que o original verifica o checksum recebido: os consumidores examinados não contêm essa validação.

Exemplos reais com ordinais da Evidence de leitura:

| Consulta | Solicitação | Corpo da resposta | Ordinais seq |
|---|---|---|---|
|Perfil atual|08 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 3F|0E 00 00 00 01 00 00 00 00 00 00 00 00 00 00 3D|2/3|
|Conexão|08 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 4A|03 00 00 00 01 01 00 00 00 00 00 00 00 00 00 47|4/5|
|Estado0F|08 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 3E|0F 00 00 00 01 01 00 00 00 00 00 00 00 00 00 3B|6/7|
|EEPROM0000,10 bytes|08 08 00 00 00 0A 00 00 00 00 00 00 00 00 00 00 3B|08 00 00 00 0A 01 54 03 52 00 55 00 55 00 55 91|8/9|
|EEPROM00B4,5 bytes|08 08 00 00 B4 05 00 00 00 00 00 00 00 00 00 00 8C|08 00 00 B4 05 54 FF FF FF FF 00 00 00 00 00 3B|44/45|

Os22 pares completos estão no JSON de resumo e na Evidence original. EEPROM0000…00B8 SHA-256 e todos os bytes estão preservados no resumo; este trecho não é dump de firmware e não permite reconstruir firmware interno.

### DR04 — estado lido, não defaults

| Campo observado | Valor e interpretação delimitada |
|---|---|
|Perfil ativo|0 na resposta0E|
|Polling|EEPROM0000=1, codec corresponde1000Hz|
|Quantidade/índice DPI|EEPROM0002=3;0004=0; refletidos no perfil em memória|
|DPI slots0…7|1200,500,1500,3200,5000,26000,26000,26000 em ambos os eixos, pelo codec3395; todos os oito registros têm checksum válido|
|LOD|000A=1|
|Debounce|00A9=3ms, diferente do default instalado8ms|
|Chave de luz|00AB=1|
|Tempo AD|00AD=30, convertido pelo host para300 segundos|
|FixLine/Ripple|00AF=1;00B1=0|
|Apagar luz ao mover|00B3=1|
|Campos B5/B7|AmbosFF, com pares FF/FF sem checksum de registro55 válido; não promover255 a opção suportada de auto-sleep/Motion Sync|

O registro DPI26000 real é `07 07 88 BF`, compatível com o caminho individual/inversor. O caminho em lote do host gera `07 07 82 C5`, conforme assembly. Isso corrobora a relevância da diferença de codificação; **não foi escrito o registro divergente** para determinar seu efeito físico. Valores de sensibilidade real medidos por deslocamento do sensor continuam UNKNOWN.

O snapshot do modelo em memória confirma CID40,MID1,sensor3395,DM6,KM efetivo6,LedMask14,ShowMainEffect1,ShowLogoEffect0,ShowXY0. Perfil corrente usa quantidade DPI3 e preserva valoresFF nos campos780/784. Portanto capacidades/configuração OEM, perfil local e estado atual do dispositivo não podem ser tratados como a mesma camada. O campo provisoriamente rotulado Sensor3395Max na sondagem de globals não teve endereço validado e não é usado como evidência do limite; o limite26000 vem do INI/loader/tabela estática.

### DR05 — correção de ShowPower

Os dois globals carregados de ShowPower estão **0 na memória real**, mas o indicador está visível. O motivo está no código:

- `0043B760` só evita mostrar o filho de bateria quando o bit1 (máscara2) está ligado. Com0, consulta bem-sucedida e percentual<101, exibe o filho.
- Painter `00446AF0` mostra percentual quando bit0 está desligado e o estado é não carregando ou carregando com percentual100.
- O outro global005F7898 não teve consumo funcional além do loader no conjunto examinado.

Logo ShowPower **não é booleano de “exibir bateria”** no caminho confirmado. A afirmação anterior “ShowPower0 oculta bateria” estava errada e foi substituída. A evidência combina branches estáticos, snapshot de globals e indicador real100%. Não presumir semântica de todos os outros bits não examinados.

### DR06 — quatro telas e ações observadas

EnumWindows encontrou a janela principal oculta mesmo quando MainWindowHandle/UIAutomation não a expunham. Ela foi mostrada pela mesma mensagem usada na instância única, sem iniciar outro processo. Foram acionados somente os quatro botões de navegação, por mensagens BM_CLICK; ações e tempos em `runtime-navigation-actions.json`, inventários de filhos por tela em `private-analysis/runtime-nav*-windows.json`.

Ordem visual observada dos botões: **teclas, DPI/avançado, macro, iluminação**. Isso não renumera os destinos internos do switch, cuja ordem é teclas/macro/DPI/LED. A separação entre ordem visual e índices internos foi confirmada em execução.

- Teclas: seis atribuições físicas listadas, seletor de perfil e ações de restaurar/exportar.
- DPI: título, valor1200 no estágio apresentado, quatro labels125/250/500/1000Hz, painel inferior de efeito DPI, LOD1/2mm e opções avançadas.
- Macro: duas listas, iniciar gravação, atraso automático, três modos de repetição, contagem e inserção de evento; listas estavam vazias.
- Iluminação: destino e controles filhos existem; a captura PrintWindow não reproduziu todos os controles owner-drawn, portanto não se afirma que a aparência parcial da imagem seja a tela real completa.

PNG privados são evidência de observação e não assets do clone; nenhuma imagem foi inserida no CLONE_SPEC para reutilização. PrintWindow e enumeração não garantem reconstrução pixel a pixel de todos os estados. O perfil foi apenas enviado ao diálogo de exportação, com destino privado explícito; a automação de salvar não concluiu, o diálogo foi cancelado e nenhum JMA de execução foi gerado. Não se promoveu por isso a validação estática do formato JMA a confirmação runtime.

### DR07 — rede e limites físicos

Foram instrumentadas connect/send/sendto no WS2_32 carregado; nenhum evento dessas APIs foi observado nas janelas de mostrar/navegar aqui retidas. WinHTTP/WinINet não estavam presentes nesses hooks. Frida pode carregar módulos auxiliares; a existência de WS2_32 no processo instrumentado não prova uso pelo aplicativo. Não houve PCAP nem teste de todos os caminhos de rede.

Há destino externo literal **http://www.a-jazz.com** em XML `tc_web`; `0043E7B0` usa ShellExecute quando o texto não é vazio. Trata-se de abertura no navegador externo, sem protocolo HTTP próprio do aplicativo demonstrado. O endereço não foi visitado; redirects, TLS e disponibilidade atual são UNKNOWN.

Permanecem sem teste físico: escrita/ACK/readback de cada ajuste, persistência após desligar, rádio sem fio, atualização/bootloader, macros em reprodução, comportamento sob falha/desconexão e medida real de DPI/LOD. Não testar um comando perigoso ou um erro não invalida a análise; impede alegar que tudo está confirmado. A conexão informada por cabo não valida o modo sem fio. Nenhum teste Linux ou clone foi executado.


## Estrutura de perfil

Fontes: Ghidra OemDrv.exe, `0044DD80` (reset), `0044DC00` (defaults), `0044DB50` (DPI), `0040F1C0` (binding), `004103E0` (codec), `0043C330` (DCT) e `0043F120`/`0043F390` (JMA); snapshot passivo PRO_4001.dct. Todos os offsets abaixo são relativos ao **início de um perfil de0x844 bytes**, sem o prefixo4 do DCT. Inteiros armazenados little-endian, exceto quando o codec USB especifica outra ordem. Tamanhos/semântica além dos campos explicitados: UNKNOWN.

| Offset | Tamanho | Campo |
|---|---:|---|
|000|4|Magic0xFCAA1234, ver import JMA.|
|004|4|Identificador/estado interno não nulo exigido no import; exportador DCT copia este campo do perfil atual para o prefixo do arquivo. Não tratar como número de perfil ou ponteiro válido no Linux.|
|008…20F|0x208|Área zerada por reset; possível associação de aplicação, sem contrato confirmado: UNKNOWN.|
|210|0x28|Nome UTF-16LE,20 wchar; reset formata no máximo19 unidades. Não confundir com nome de macro40 wchar.|
|238|4|Banco de teclas selecionado, reset0.|
|23C|0x180|Banco0 de16 registros de binding×24 bytes.|
|3BC|0x180|Banco1.|
|53C|0x180|Banco2.|
|6BC|4|Código de polling0x125/0x250/0x500/0x1000.|
|6C0|4|Rolagem:1..10 linhas ouFFFFFFFF página inteira;00409240.|
|6C4|4|Tempo de duplo clique em ms;00409240.|
|6C8|4|Velocidade de ponteiro Windows, tabela discreta;00409240.|
|6CC|4|Precisão/aceleração do ponteiro, booleano;00428950.|
|6D0|4|Rastro Windows, default0; controle visível correspondente não confirmado.|
|6D4|4|Estado XY independente candidato; reset0 em0044DB50. Não é o primeiro campo de um registro DPI.|
|6D8+i×10h|4|DPI X, para i0…7.|
|6DC+i×10h|4|DPI Y.|
|6E0+i×10h|4|Cor de estágio.|
|6E4+i×10h|4|Flag por estágio; default dos estágios configurados0 e dos outros1 em0044DB50. Interpretação apoiada como desabilitado/oculto, confirmar todos os usos antes de impor semântica de boolean no import.|
|758|4|Índice de DPI atual colocado pelo export JMA; não necessariamente estado continuamente mantido em toda cópia de perfil.|
|75C|4|Identificador de sensor,0x3395 nesta instalação.|
|760|4|Quantidade de estágios a apresentar/configurar, de DpiUILevels ou DM; default6.|
|764|4|LOD; reset a ShowLOD como valor inicial, sem prova de unidade física.|
|768|4|Ripple; reset0.|
|76C|4|FixLine/correção de ângulo; reset0.|
|770|4|Tempo de economia/sleep; codec divide por10.|
|774|4|Debounce; default efetivo8.|
|778|4|Apagar luz ao mover; default de dispositivo.|
|77C|4|Chave de luz, reset1.|
|780|4|Campo associado a Motion Sync candidato, reset1; habilitação UI é separada.|
|784|4|Auto-sleep em dezenas de segundos, tabela1,2,3,6,12…60; reset6=60s;00409A10/0040A210. Resposta física específica permanece UNKNOWN.|
|788/78C/790|4 cada|Parâmetros de efeito DPI extraídos de DpiLEDMode, não confundir com modo LED principal.|
|7C0/7C4/7C8/7CC|4 cada|Modo/velocidade/brilho/COLORREF principal, respectivamente;0041AC20. Bytes restantes até7F7 permanecem parcialmente UNKNOWN.|
|7F8…82F|0x38|Parâmetros secundários/logo, inicializados como cópia com limites adicionais; ShowLogoEffect=0 nesta instalação.|
|830…843|0x14|UNKNOWN.|

Os campos DPI no snapshot passivo eram originalmente interpretados como grupos flag/X/Y/cor a partir de um endereço quatro bytes anterior. A correlação com o escritor de defaults resolve a ambiguidade: os registros lógicos começam em6D8 com **X/Y/cor/flag**, e6D4 é separado. Não promover o agrupamento visual inicial do hexdump a formato definitivo.

Registro de binding em banco+índice×0x18:

| Relativo | Tamanho | Conteúdo |
|---|---:|---|
|+0|4|byte alto=classe/major;24 bits baixos=função/minor. Exemplo default esquerdo01000011h.|
|+4|4|Índice físico/de matriz, geralmente1-based, vide defaults K e inversor0040F1C0 que subtrai1.|
|+8|4|Referência de macro/ID ou dado lógico da ação.|
|+C|4|Modificadores/parâmetros de combinação.|
|+10|4|Argumentos especiais ou slots de combinação.|
|+14|4|Argumentos adicionais.|

Classe01 mouse,02/03/04 ações de teclado/combinação/mídia encaminhadas para codec5,05 macro,08 especiais,0B função bruta aparecem em004103E0. Significado de todos os bits internos e slots de combinações depende do codec correspondente; preservar como UNKNOWN para classes não reconhecidas.

DCT contém prefixo4 seguido de até4 desses blocos. JMA contém um bloco e dez macros em claro. Não há serialização explícita portátil campo a campo nos caminhos examinados: é escrita de imagem de estrutura. O clone deve manter seu próprio formato nativo e um importador limitado a este layout conhecido; isso é escolha de projeto Linux, não exigência de usar a estrutura Windows em memória.


## Macros, combinações e intercâmbio

### Evidência e confiança

Análise estática do export Ghidra `private-analysis/OemDrv.exe.decompiled.txt` e das strings/referências de `OemDrv.exe.inventory.txt`, alvo SHA-256 `ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846`, x86 little-endian, base 0x00400000. Os endereços abaixo são VAs do executável. Não executei o alvo, não gerei arquivos de entrada para ele e não copiei código/ativos. A exportação integral do conjunto reconhecido foi concluída; funções citadas abaixo foram lidas com seu limite seguinte. Protótipos, nomes de variáveis locais e pilha recuperada pelo decompilador apresentam erros; resultados abaixo priorizam constantes, offsets, operações e chamadas reconhecíveis. Traduções de nomes são interpretações, não símbolos originais.

### .jmm: macro individual

**Confirmado estaticamente:** leitura e escrita de um bloco fixo de **0x342 = 834 bytes**. `00421990` lê exatamente essa quantidade e rejeita falha/leitura curta; não há verificação visível de EOF, portanto arquivo maior pode ser aceito pelo prefixo. `00422660` escreve exatamente 834 e verifica também o total escrito. `00421E20` exporta copiando o arquivo existente com `CopyFileW(..., false)`; o export individual não reserializa o conteúdo nesse caminho.

O arquivo aplica rotação de bits independente a cada byte: codificação **ROR8 por 2**, decodificação **ROL8 por 2**. `00422D90` codifica e `00422DB0` decodifica, ambos em 834 bytes. A varredura de pasta `004227A0` contém a mesma decodificação explicitamente. Isto é ofuscação reversível, sem evidência de criptografia, compressão ou checksum nesse contêiner. Magic decodificado **0xFACB99A0**, bytes little-endian `A0 99 CB FA`; os quatro bytes correspondentes no arquivo rotacionado são `28 66 F2 BE`.

Layout da macro **decodificada**, derivado do construtor `0044D7C0`, edição `0041DB80`, captura `004212D0`, renderização `004214D0` e validação `00422200`:

| Offset | Tamanho | Significado e evidência |
|---|---:|---|
| 0x000 | 4 | Magic 0xFACB99A0; `00420E80`, `00421990`, `0043F8D0` |
| 0x004 | 4 | ID da macro; consultas `0044D930`, geração `0044D9B0` |
| 0x008 | 4 | Flags; bits 0x40000000 e 0x80000000 sinalizam opções/eventos alterados em `0041D160`, `0041DB80`; `00422660` limpa esses dois antes de salvar |
| 0x00C | 4 | Estado de atraso automático, copiado do controle em `0041DB80`; construtor inicializa 1, interpretação apoiada pelo uso do mesmo controle na gravação `0041F330` |
| 0x010 | 4 | Modo de repetição: 0=número de ciclos; 2=até soltar; 1=até qualquer tecla. Correlação da seleção dos controles `0041D9E0`/`0041DB80` com os rótulos `tc_macro_loop1/2/3`; modalidade 1 versus 2 exige essa correlação, não apenas o inteiro |
| 0x014 | 0x50 | Nome UTF-16LE, buffer 40 wchar; formatação com limite de 39 caracteres em `0044D7C0`/`00421990` |
| 0x064 | 4 | Campo inicializado zero; significado não estabelecido |
| 0x068 | 2 | Contagem de ciclos uint16; inicial 1; edição zero vira 1 (`0041DB80`); controle restringe visualmente 1–250 em `0041D260` |
| 0x06A | 0x2D8 | 91 registros estruturais de 8 bytes; a capacidade da interface é menor, ver abaixo |

Registro em `0x06A + i*8`:

| Offset relativo | Tamanho | Significado |
|---|---:|---|
| +0 | 2 | Tecla/código ou dois componentes de movimento |
| +2 | 2 | Flags: 0=soltar, 1=pressionar; bit 1 indica movimento (valor 2 produzido pelo serializador) |
| +4 | 4 | Atraso após o evento, em ms; zero omite linha de atraso na interface |

`004212D0` transforma lista em registros: eventos de teclado usam apenas o byte baixo do código; movimento retém uint16; atraso é incorporado ao evento anterior. `004214D0` usa o código e atraso iguais a zero como término e limita a quantidade exibida. Movimento interpreta o byte baixo/alto como componentes com sinal, via `00421410`; `00420220` monta o valor com dois bytes. Não concluir sem análise do protocolo que a unidade seja pixel físico ou que firmware e contêiner usem o mesmo formato.

**Limites confirmados no caminho inicial:** `0044D070` define `DAT_0060BC04=0x46` (**70 eventos**), `DAT_0060BC00=0xFFFF` (**65535 ms**). `0041F2B0` conta pressionar/soltar/movimento e exclui linhas de atraso do limite. `004214D0` limita o render a esse global, com fallback de 90 se zero ou >=90. Portanto 91 slots físicos não significam 91 eventos editáveis. Não foi provada invariância desses globals durante toda a execução.

`0044B7F0` lê `MinDelay` (default 10) em `DAT_005F78F0`; instalação define 1 em Cfg.ini. `0044D070` copia esse mínimo para `DAT_0060BBF0`. `0044B7F0` também lê `MinUIDelay` (default 1) em `DAT_005F791C`. `0041F330` usa esse último mínimo para atraso automático e teto 65535; inserção manual (`00420220`, ação 0xF9) oferece 1–65535 e ajusta para mínimo de dispositivo. A diferença entre esses dois mínimos deve ser preservada como distinção. `00420F80` normaliza a lista antes de serializar: remove itens iniciais até pressionar, agrega atrasos adjacentes e elimina duplicados adjacentes de mesmo tipo/código.

### Validações e operações de macro

- `0041DE30`: criação bloqueada quando contador `DAT_005DEDE0 >= 2000`; checa seleção de pasta, diálogo de nome e duplicidade sob mesmo pai.
- `0041DCA0`: rejeita nome vazio e caracteres `/`, `\`, `?`, `+`, `=`, `-`, `*`, `&`, `%`, `!`, `#`; corta o sufixo a partir do último ponto encontrado. O decompilador recuperou retorno como void apesar de chamadores testarem resultado; não depender desse protótipo.
- `00421990`: importar .jmm; checa duplicidade pelo título no destino, abre arquivo, exige 834 bytes lidos, decodifica, checa magic e chama `00422200`. Nome interno é substituído pelo título importado, novo ID é gerado e macro é gravada na árvore/pasta de destino.
- `00422200`: percorre códigos 0xF0…0xF6 até código zero, exige respectivamente bits 1,2,4,8,0x10,0x20,0x40 em `DAT_0060B348`. Para configuração `MacroHasMsKey=0x07`, apenas os três primeiros dessa família são autorizados. Este validador não contém limite explícito de registros ou validação geral de códigos de teclado; não copiar sua permissividade para um parser novo.
- Strings de erro estão ligadas por xrefs a essas funções: abrir/ler falhou, macro inválida, tecla sem suporte; `00422660` registra erro de caminho/escrita e controla flags dirty.
- `004222A0`: caminho deriva de raiz do aplicativo + `Mac`, pastas da árvore e `\nome.jmm`; buffers tradicionais 260 wchar e caminhada de no máximo 20 ancestrais. Não são prova de profundidade oficialmente suportada.
- `0041EF40`/`0041F080`: exportação/importação em lote escolhem diretórios, usam cópia/varredura de pastas, não um arquivo de arquivo compactado. A rotina recursiva `004227A0` testa conteúdo/magic, não depende somente de extensão; pastas começando com `.` ou `$` são puladas no caminho recursivo observado. Associação exata de imagens/ícones de pastas é secundária e não necessária ao formato.
- Gravação `00421FE0` reconhece WM_KEYDOWN/UP e SYSKEYDOWN/UP, normaliza modificadores direitos via bits de lParam; `0041F330` evita evento idêntico consecutivo e calcula atrasos com GetTickCount. Isso documenta o capturador Windows; captura equivalente no Linux ainda exige implementação independente.

### .jma: exportação/importação de perfil

`0043F120` exporta **0x28D8 = 10456 bytes**, sem a rotação .jmm. Copia o perfil atual de **0x844 = 2116 bytes** e acrescenta slots contendo macros **decodificadas**, não arquivos .jmm codificados. Aritmética: 2116 + 10×834 = 10456. A área é zerada antes do preenchimento. Exportação coloca DPI atual em perfil+0x758 (`[0x1D6]`).

| Offset do .jma | Tamanho | Conteúdo observado |
|---|---:|---|
| 0x0000 | 0x844 | Bloco de perfil opaco nesta análise; magic inicial 0xFCAA1234, uint32+4 não zero é condição de aceitação |
| 0x0844 | 0x2094 | Dez slots de macro de 834 bytes em claro, cada qual no layout acima |

`0043F390` abre/lê 10456 bytes, mas **só rejeita retorno zero**: a condição de tamanho exato, presente em .jmm, não foi observada aqui. Em seguida exige magic `0xFCAA1234` e campo+4 !=0. Não foi encontrado checksum ou validação de tamanho/compatibilidade de cada campo no importador examinado. Isso é descrição de uma limitação do leitor, não recomendação de reproduzi-la.

Percorre **3 bancos ×16 posições**, stride 0x18 (24) bytes. A primeira checagem de ação está em perfil+0x23F; macro é tipo 5; primeiro ID referenciado está em +0x244. Para cada referência procura o ID entre os dez slots. Se encontra macro local com mesmo ID, `0043F880` substitui seu conteúdo, preserva ID e regrava .jmm por `0043F780`. Se não encontra macro local, gera ID novo, adiciona via `0043F8D0` e atualiza referência no perfil. Portanto importar perfil pode **alterar uma macro existente de mesmo ID**, além de criar outras.

Após processamento copia somente os 2116 bytes de perfil, preserva o campo local +4, recupera DPI atual de +0x758 e ajusta para zero se fora de `[0, quantidade de estágios)`. Chama atualização de interface e aplicação do perfil; detalhes de transporte ficam fora desta tarefa.

**Cautela de cobertura:** o export percorre 48 atribuições e incrementa índice de macro a cada referência localizada. Não há teste explícito de `<10` nem deduplicação visível nessa rotina, apesar de o arquivo acomodar dez slots. Não afirmar suporte seguro a 48 macros exportadas nem reproduzir esse comportamento. Arquivos importados com referências a IDs não presentes nos dez slots não têm rejeição explícita no laço observado. Não foi demonstrada validação de teclas `00422200` nesse caminho de perfil, ao contrário do import individual.

### mac.dct: cache agregado

`0044DA00` cria/trunca arquivo `raiz + mac.dct`, zera buffer e grava sempre **0x1973A0 = 1668000 bytes**, exatamente **2000×834**. Percorre lista global de macros, copiando apenas entradas cujo ponteiro é válido, ID+4 não zero e primeiro código em +0x6A não zero. Para ao juntar 2000. Restante fica preenchido com zeros. Não chama rotação ao copiar/gravar: o contêiner contém macros **decodificadas**. Não há cabeçalho de quantidade separado nesse escritor; os registros são concatenados desde offset zero.

Não foi localizada rotina leitora para mac.dct nos xrefs de sua string, nem segundo literal de nome. O caminho de carregamento da árvore examinado usa pasta `Mac` e .jmm. **UNKNOWN:** se mac.dct é lido por outro componente, usado exclusivamente como cache auxiliar, e quais flags dirty podem permanecer nesse arquivo. Não descrever mac.dct como fonte única de persistência.

### Identificadores e conflitos

`0044D9B0` dorme 20 ms, lê hora local e combina bits de hora/minuto/segundo/milissegundo; não é UUID nem contador monotônico. O decompilador agrupa campos SYSTEMTIME em DWORDs sobrepostos, portanto não foi promovida a fórmula de ID a contrato completo. `00420D80` compara o ID na lista com 24 bits de referência da árvore; confirmar com o código de árvore antes de impor limite geral de ID. `0043F880` confirma igualdade de ID ao substituir conteúdo no import de perfil.

### Macro no dispositivo: estrutura separada do .jmm

`00410BB0` converte macro de software para buffer de **0x180=384 bytes**, com até **70 eventos** de cinco bytes e cabeçalho de 32 bytes; tamanho útil inferido das operações de cópia é **L=32+5N**. O decompilador mostra retorno void, mas o chamador `00410EE0` usa um comprimento retornado; a combinação desses caminhos, não o protótipo recuperado, fundamenta o tamanho. N=70 ocupa382 bytes úteis, checksum em382 e byte383 zerado no buffer. Assembly da segunda passagem confirmou que esse último byte não é enviado: transferência383 bytes; paraN<=69, comprimento enviadoL+4.

| Offset | Conteúdo observado |
|---|---|
| 0x00 | Quantidade de **bytes** de nome: 2×min(comprimento,15), preenchida pelo aplicador |
| 0x01…0x1E | Até 15 unidades UTF-16LE do nome; não é o campo de 39 unidades do .jmm |
| 0x1F | Número N de eventos, atribuído pelo conversor |
| 0x20+5i | Tipo/direção do evento |
| 0x21+5i | Código HID/máscara/byte X |
| 0x22+5i | Zero em tecla/mouse; byte Y em movimento |
| 0x23+5i | Byte alto do atraso |
| 0x24+5i | Byte baixo do atraso; **atraso big-endian uint16**, diferente do uint32 little-endian .jmm |
| L | Byte checksum, definido pelo chamador |

Para teclas/botões, byte de evento é `0x40|família` ao soltar e `0x80|família` ao pressionar. Famílias: 0=modificador, 1=tecla HID, 4=botão mouse; movimento usa tipo 5 e dois bytes de deslocamento. Mapeamento mouse: software F0→máscara1, F1→2, F2→4, F3→0x10, F4→8. Não há casos F5/F6 nesse conversor; em vez disso caem na busca genérica HID. Não promover suporte deles em hardware com base no XML.

Modificadores: Ctrl esquerdo/genérico→1, Shift esquerdo/genérico→2, Alt esquerdo/genérico→4, Windows esquerdo/direito→8, Ctrl direito→0x10, Shift direito→0x20, Alt direito→0x40. Outras teclas pesquisam tabela de 104 pares em VA `005B2EB8` (HID) / `005B2EB9` (código Windows); tabela completa no anexo deste capítulo. Código não encontrado produz zero e diagnóstico, sem retorno de erro explícito nesse caminho.

`00410910` faz inverso, recebendo ponteiro na **contagem em 0x1F** (eventos a seguir), limita N pelo global 70 e reconstrói registros em +0x6A. Atraso do último evento não é copiado: rotina retorna imediatamente após completar a contagem, antes da atribuição de atraso. Conversões software↔hardware podem portanto perder informação (nome truncado, Win direito fundido e atraso final omitido).

**Checksum e ordem:** `00410EE0` soma bytes do buffer ainda com cabeçalho de nome zerado e grava `0x55 − soma(bytes[0:L]) mod 256` em offset L. **Somente depois preenche comprimento e nome**. Logo não se deve validar soma de todo o bloco final com nome contra 0x55 sem reproduzir essa exclusão/ordem. Rotinas de nome e checksum podem pertencer a regiões lógicas independentes; confirmar semântica de leitura do firmware com a análise de protocolo. Após checksum, até três zeros são escritos quando L+1<382.

Aplicação usa `00450DC0` com endereço **(índice_de_matriz×3+6)×0x80 = 0x300 + índice×0x180**. Matriz associa macro por palavra do tipo 6, acrescentando índice no byte seguinte; modo/contagem vêm da tradução de binding `004103E0` (analisada pelo agente principal). Não há ID .jmm transportado nesse corpo. A rotina principal escreve macros antes de gravar matriz com `00451640`; possui esperas de 10ms entre operações. Não observei execução desses caminhos.

### Combinações de teclas no dispositivo

`00410680` gera payload separado de macro, `0040EEA0` interpreta seu inverso e `00410EE0` aplica com endereço **(índice+8)×0x20 = 0x100+índice×32**. Byte inicial é contagem e registros têm **3 bytes**, sem atraso: tipo, código baixo, código alto/zero. Modificadores usam pressionar0x80/soltar0x40 com máscara1/2/4/8; teclas HID pressionar0x81/soltar0x41. Ordem: pressionar modificadores Ctrl/Shift/Alt/Win, pressionar até três teclas em ordem de slots, soltar modificadores nessa ordem, soltar teclas em ordem inversa. O leitor para ao chegar ao primeiro registro com direção 0x40 e acumula só os pressionamentos; retém até três teclas e máscara de modificadores.

Para ações multimídia/sistema, o escritor gera dois registros com família2: `[0x82,usage_lo,usage_hi]` e `[0x42,usage_lo,usage_hi]`; comprimento7 contando byte de quantidade=2. O usage vem de `00410590`, cujo catálogo completo permanece com a análise de bindings do agente principal. `0040EEA0` reconhece usages de mídia e aplicações e os converte para funções internas. O aplicador acrescenta checksum 0x55−soma no primeiro byte após payload; não há nome nesse bloco. Combinações grandes envolvendo quatro modificadores mais três teclas podem gerar mais que os 32 bytes reservados por índice; o limite real da UI e do escritor de EEPROM exige correlação adicional antes de expor todas essas combinações.

### UNKNOWNs restantes

Campos de perfil além dos offsets explicitados; campo macro+0x64; bits baixos das flags; escrita/leitura de versões históricas; uso e leitor de mac.dct; estabilidade global dos limites 70/65535; mapeamento completo dos códigos 0xF0–0xF6 para botões/roda; tratamento prático de arquivos truncados ou referências ausentes; comportamento após erro de gravação; Unicode além de 39 unidades UTF-16; realinhamento ou unidade do movimento no firmware; conflitos de ID gerados na mesma janela temporal; atomicidade de salvamento. Nenhum arquivo de exemplo .jmm/.jma foi validado contra execução real neste trabalho.

Para um parser Linux independente: tratar magic, tamanho, limites de registro, terminação de nome e referências como verificações próprias explícitas; preservar campos desconhecidos somente quando a versão estiver identificada. Essas são recomendações de implementação, não comportamento observado do original.

### Anexo — tabela HID / código virtual Windows integral

Tabela estática de 104 pares consultada por `00410BB0`, `00410680` e inversa `00449310`: VA `0x005B2EB8`, seção `.rdata`, offset de arquivo `0x1B1EB8`, 208 bytes. SHA-256 desse intervalo `5b983fb0b6f1c6fabd621faaaf8e64f0c697c6de39e2be7290aa03519a697ff0`. Cada par é HID primeiro e VK Windows depois. Não são keycodes evdev; para Linux é necessária tradução semântica independente. Pares mantêm ordem e duplicidades do original.

| Índice | VA do par | HID | VK Windows |
|---:|---|---|---|
| 0 | 005B2EB8 | 0x29 | 0x1B |
| 1 | 005B2EBA | 0x3A | 0x70 |
| 2 | 005B2EBC | 0x3B | 0x71 |
| 3 | 005B2EBE | 0x3C | 0x72 |
| 4 | 005B2EC0 | 0x3D | 0x73 |
| 5 | 005B2EC2 | 0x3E | 0x74 |
| 6 | 005B2EC4 | 0x3F | 0x75 |
| 7 | 005B2EC6 | 0x40 | 0x76 |
| 8 | 005B2EC8 | 0x41 | 0x77 |
| 9 | 005B2ECA | 0x42 | 0x78 |
| 10 | 005B2ECC | 0x43 | 0x79 |
| 11 | 005B2ECE | 0x44 | 0x7A |
| 12 | 005B2ED0 | 0x45 | 0x7B |
| 13 | 005B2ED2 | 0x04 | 0x41 |
| 14 | 005B2ED4 | 0x05 | 0x42 |
| 15 | 005B2ED6 | 0x06 | 0x43 |
| 16 | 005B2ED8 | 0x07 | 0x44 |
| 17 | 005B2EDA | 0x08 | 0x45 |
| 18 | 005B2EDC | 0x09 | 0x46 |
| 19 | 005B2EDE | 0x0A | 0x47 |
| 20 | 005B2EE0 | 0x0B | 0x48 |
| 21 | 005B2EE2 | 0x0C | 0x49 |
| 22 | 005B2EE4 | 0x0D | 0x4A |
| 23 | 005B2EE6 | 0x0E | 0x4B |
| 24 | 005B2EE8 | 0x0F | 0x4C |
| 25 | 005B2EEA | 0x10 | 0x4D |
| 26 | 005B2EEC | 0x11 | 0x4E |
| 27 | 005B2EEE | 0x12 | 0x4F |
| 28 | 005B2EF0 | 0x13 | 0x50 |
| 29 | 005B2EF2 | 0x14 | 0x51 |
| 30 | 005B2EF4 | 0x15 | 0x52 |
| 31 | 005B2EF6 | 0x16 | 0x53 |
| 32 | 005B2EF8 | 0x17 | 0x54 |
| 33 | 005B2EFA | 0x18 | 0x55 |
| 34 | 005B2EFC | 0x19 | 0x56 |
| 35 | 005B2EFE | 0x1A | 0x57 |
| 36 | 005B2F00 | 0x1B | 0x58 |
| 37 | 005B2F02 | 0x1C | 0x59 |
| 38 | 005B2F04 | 0x1D | 0x5A |
| 39 | 005B2F06 | 0x1E | 0x31 |
| 40 | 005B2F08 | 0x1F | 0x32 |
| 41 | 005B2F0A | 0x20 | 0x33 |
| 42 | 005B2F0C | 0x21 | 0x34 |
| 43 | 005B2F0E | 0x22 | 0x35 |
| 44 | 005B2F10 | 0x23 | 0x36 |
| 45 | 005B2F12 | 0x24 | 0x37 |
| 46 | 005B2F14 | 0x25 | 0x38 |
| 47 | 005B2F16 | 0x26 | 0x39 |
| 48 | 005B2F18 | 0x27 | 0x30 |
| 49 | 005B2F1A | 0x2B | 0x09 |
| 50 | 005B2F1C | 0x39 | 0x14 |
| 51 | 005B2F1E | 0x28 | 0x0D |
| 52 | 005B2F20 | 0x2A | 0x08 |
| 53 | 005B2F22 | 0x2C | 0x20 |
| 54 | 005B2F24 | 0x2F | 0xDB |
| 55 | 005B2F26 | 0x30 | 0xDD |
| 56 | 005B2F28 | 0x31 | 0xDC |
| 57 | 005B2F2A | 0x33 | 0xBA |
| 58 | 005B2F2C | 0x34 | 0xDE |
| 59 | 005B2F2E | 0x36 | 0xBC |
| 60 | 005B2F30 | 0x37 | 0xBE |
| 61 | 005B2F32 | 0x38 | 0xBF |
| 62 | 005B2F34 | 0x35 | 0xC0 |
| 63 | 005B2F36 | 0x2E | 0xBB |
| 64 | 005B2F38 | 0x2D | 0xBD |
| 65 | 005B2F3A | 0x46 | 0x2C |
| 66 | 005B2F3C | 0x47 | 0x91 |
| 67 | 005B2F3E | 0x48 | 0x13 |
| 68 | 005B2F40 | 0x49 | 0x2D |
| 69 | 005B2F42 | 0x4A | 0x24 |
| 70 | 005B2F44 | 0x4B | 0x21 |
| 71 | 005B2F46 | 0x4C | 0x2E |
| 72 | 005B2F48 | 0x4D | 0x23 |
| 73 | 005B2F4A | 0x4E | 0x22 |
| 74 | 005B2F4C | 0x52 | 0x26 |
| 75 | 005B2F4E | 0x51 | 0x28 |
| 76 | 005B2F50 | 0x50 | 0x25 |
| 77 | 005B2F52 | 0x4F | 0x27 |
| 78 | 005B2F54 | 0x59 | 0x61 |
| 79 | 005B2F56 | 0x5A | 0x62 |
| 80 | 005B2F58 | 0x5B | 0x63 |
| 81 | 005B2F5A | 0x5C | 0x64 |
| 82 | 005B2F5C | 0x5D | 0x65 |
| 83 | 005B2F5E | 0x5E | 0x66 |
| 84 | 005B2F60 | 0x5F | 0x67 |
| 85 | 005B2F62 | 0x60 | 0x68 |
| 86 | 005B2F64 | 0x61 | 0x69 |
| 87 | 005B2F66 | 0x62 | 0x60 |
| 88 | 005B2F68 | 0x57 | 0x6B |
| 89 | 005B2F6A | 0x56 | 0x6D |
| 90 | 005B2F6C | 0x55 | 0x6A |
| 91 | 005B2F6E | 0x54 | 0x6F |
| 92 | 005B2F70 | 0x53 | 0x90 |
| 93 | 005B2F72 | 0x58 | 0x0D |
| 94 | 005B2F74 | 0x63 | 0x6E |
| 95 | 005B2F76 | 0xE0 | 0xA2 |
| 96 | 005B2F78 | 0xE1 | 0xA0 |
| 97 | 005B2F7A | 0xE2 | 0xA4 |
| 98 | 005B2F7C | 0xE3 | 0x5B |
| 99 | 005B2F7E | 0xE4 | 0xA3 |
| 100 | 005B2F80 | 0xE5 | 0xA1 |
| 101 | 005B2F82 | 0xE6 | 0xA5 |
| 102 | 005B2F84 | 0xE7 | 0x5C |
| 103 | 005B2F86 | 0x65 | 0x5D |

### Anexo — mídia e aplicações: usages e rótulos

Mapeamento de `00410590` e `0040EEA0`, correlacionado com rótulos de mídia/aplicações nos XMLs (catálogo integral em RESOURCE_FINDINGS.md). São usages transportados pela família2 dos registros de combinação; byte baixo precede alto. A interface pode filtrar escolhas por modelo.

| Função interna baixa | Usage | Rótulo / chave de recurso |
|---|---|---|
| 0x21 | 0x0183 | Reprodutor de mídia / tc_kbmedia_msel |
| 0x22 | 0x00CD | Reproduzir/Pausar / tc_PL |
| 0x23 | 0x00B7 | Parar reprodução / tc_stop |
| 0x24 | 0x00B6 | Anterior / tc_pre_media |
| 0x25 | 0x00B5 | Próxima / tc_next_media |
| 0x26 | 0x00E9 | Aumentar volume / tc_vol_up |
| 0x27 | 0x00EA | Diminuir volume / tc_vol_dw |
| 0x28 | 0x00E2 | Silenciar / tc_mute |
| 0x30 | 0x018A | Email / tc_kbmedia_mail |
| 0x31 | 0x0192 | Calculadora / tc_kbmedia_cal |
| 0x32 | 0x0194 | Explorador / tc_kbmedia_explore |
| 0x33 | 0x0221 | Pesquisar / tc_kbmedia_search |
| 0x34 | 0x0223 | Página inicial / tc_kbmedia_main |
| 0x35 | 0x0224 | Voltar (navegação) / tc_back |
| 0x36 | 0x0225 | Avançar (navegação) / tc_forward |
| 0x37 | 0x0226 | Parar navegador / tc_kbmedia_stop |
| 0x38 | 0x0227 | Atualizar / tc_kbmedia_refresh |
| 0x39 | 0x022A | Favoritos / tc_kbmedia_favor |

Os rótulos de navegação voltar/avançar também existem como botões mouse, mas os usages0x224/0x225 são ações da família de aplicações. Não confundir com máscaras mouse8/16.

### Anexo — correlação de ações com rótulos, revisada por assembly

O arquivo `private-analysis/ui-targeted-assembly.txt` permite ligar leitura da chave XML ao global de texto; menu e formatador de ações ligam esse global ao ID interno, e `004103E0` liga ID interno ao código de matriz. Esta cadeia resolve nomes sem inferir semântica a partir do número.

| Ação | Chave → global (VAs de instruções) | ID interno | Matriz |
|---|---|---|---|
| DPI + | tc_dpiadd, PUSH00432903 → MOV ECX,D560 em00432938 | 080000A8 | 000202 |
| DPI − | tc_dpisub,00432974 → D564 em004329A9 | 080000A9 | 000302 |
| Ciclo DPI | tc_dpiloop,004329E5 → D568 em00432A1A | 080000AA | 000102 |
| Ligar/desligar RGB | tc_rgb,00432BA9 → D574 em00432BDE | 080000A7 | 000008 |
| Alternar polling | tc_reportsw,00432DDE → D588 em00432E13 | 080000AC | 000007 |
| Alternar perfil | tc_prosw,00432FA2 → D594 em00432FD7 | 080000B0 | 000009 |
| Bloqueio DPI | tc_snipe,00432C1A → D578 em00432C4F | 080000A6 | Tipo0A; valor DPI codificado no byte seguinte |
| Clique duplo esquerdo | tc_dbclick,00431BC5 → D3C0 em00431BFA | 01000016 | 023204 |
| Três cliques | tc_three → D56C, correlacionado com formatador de ação e sequência de loader | 01000017 | 033204 |

Os códigos de DPI não seguem a ordem intuitiva +/−/ciclo=102/202/302: a correlação comprovada é **202/302/102**. Roda para cima/baixo carregam rótulos D3C8/D3CC e códigos de macro F5/F6; não aparecem como casos diretos no codificador de matriz examinado. Não atribuir-lhes 023204/033204.


## Instalação e desinstalação

Escopo: InitSetup.dll, uninstall.dll, unins000.exe e unins000.dat. Copias privadas em inputs; originais intactos; nenhum alvo foi executado. Ghidra 12.2, projeto Helpers, ExportEvidence.java. REA 6.7.0 rejeitou o provedor Ghidra 12.2: decompilacao direta no Ghidra, sem atribui-la a REA. Inventarios PE de recursos foram produzidos autenticamente por REA.

### Identidade e recursos

| Arquivo | SHA-256 | REA Evidence ID | Recursos |
|---|---|---|---|
| InitSetup.dll | 72f5cfe575253eaff31e27ce8f70b4caaa079d2c42a4130515eecf7f0967115d | ev_6910bc164ddf7ab9b5eede48eeef9cb38fd22852880504786b2ce11b8fccb704 | 2 |
| uninstall.dll | 64c8831379fed7f9ab3221b44cb6dba8bf3a5e45cd9308f4c8ae5cf2c7c2b536 | ev_9276110471e35242afb2b2191185a80076bb4ec4d652350bb080369ae5d7c6a0 | 11 |
| unins000.exe | c7b7ff4119af4036ca995b3862fecfd482a3215f535467bb9e84010a5393bbe5 | ev_f26a3d870683791bd7341a61aae5a8a4391b981b08b6a3f407b43cf60d57e3f2 | 72 |
| unins000.dat | 649ef6f4fa1cf2701125a2513d504dfa27457014f6c227b0d381828b7fe91d4a | parser local, sem Evidence ID REA | nao aplicavel |

JSONs REA em private-analysis/*.rea-resources.json: cobertura integral das arvores de recursos, payloads fora de grupos de icones opacos. Cobertura da arvore nao significa comportamento integral.

### InitSetup.dll

SetupInit, VA 0x10001080, recebe caminho UTF-16. Argumento NULL: registra erro e retorna 0. PathFileExistsW falso: registra caminho ausente e retorna 1. Caso contrario chama FUN_100010f0(caminho,0) e retorna 1 mesmo sem demonstrar sucesso da limpeza. Portanto retorno externo 1 nao certifica exclusao bem-sucedida.

FUN_100010f0, VA 0x100010f0: FindFirstFileW/FindNextFileW, ajuste de atributos, DeleteFileW, recursao em diretorios, RemoveDirectoryW quando profundidade >0. Inferencia forte: limpa conteudos preservando o diretorio inicial, pois SetupInit passa profundidade zero. Caminho vem do chamador; a DLL nao demonstra AppData fixo. O pseudocodigo tem inconsistencias de assinatura/pilha/buffers: condicao exata de exclusao de entradas especiais e retornos internos permanecem UNKNOWN sem assembly. Nao copiar literalmente esse pseudocodigo.

FUN_10001020 (0x10001020) formata log e chama OutputDebugStringW. Mensagens de NULL, caminho ausente, remocao concluida e falha DeleteFile/GetLastError.

Sem chamadas especificas de registro, INI ou rede encontradas nos imports e 234 funcoes reconhecidas. Busca limitada ao codigo identificado, nao prova ausencia absoluta de resolucao dinamica.

Fontes: private-analysis/InitSetup.dll.decompiled.txt e .inventory.txt. Cobertura: 234/234 funcoes reconhecidas decompiladas.

### uninstall.dll

FUN_10001000 (0x10001000) retorna 1 sem efeitos observaveis. Restante das 25 funcoes: CRT, cookie, validacao PE, excecoes e wrappers MSVCR90. entry 0x100013a2; ___DllMainCRTStartup 0x1000128c. Sem exportacao de remocao especifica identificada, nem chamadas de registro/arquivos/rede nos imports. Inferencia: modulo minimo com inicializacao CRT; o nome sozinho nao demonstra rotina de desinstalacao.

Fontes: private-analysis/uninstall.dll.decompiled.txt e .inventory.txt. Cobertura 25/25 funcoes reconhecidas decompiladas. UNKNOWN: proposito de empacotamento e codigo nao reconhecido.

### unins000.exe

PE x86 Borland/Delphi, engine Inno Setup. Manifesto identifica JR.Inno.Setup e descricao Inno Setup; strings de mensagens nao certificam versao integral do produto AJ199.

FUN_004f47d8 (0x004f47d8), parser: /Log ativa 0x00502f46; /VERYSILENT ativa 0x00502f48; /NoRestart ativa 0x00502f49. /SuppressMsgBoxes so ativa a supressao final com modo silencioso. FUN_004f5384 (0x004f5384) consulta callback UninstallNeedRestart, estado de reinicio e NoRestart antes de reinicio automatico.

FUN_004b4e74 (0x004b4e74) percorre registros tipados de remocao: arquivos, diretorios, registro, Exec/ShellExec e outras capacidades genericas. A lista AJ199 efetiva foi resolvida no DAT abaixo; a presenca de uma capacidade no engine nao implica seu uso pelo produto.

FUN_0047f8e0 (0x0047f8e0) usa RegDeleteKeyW quando o primeiro argumento difere de 2; no outro caso resolve RegDeleteKeyExW dinamicamente em advapi32.dll e retorna 0x7f se indisponivel. FUN_0047f978 (0x0047f978) enumera subchaves com RegEnumKeyExW, recorre e remove a chave.

Ghidra avisou relocation invalida RVA 0x109000 e metadados TLS/export inconsistentes. Analise, exportacao, pos-analise e salvamento terminaram com sucesso: 4355/4355 funcoes reconhecidas decompiladas. Isso nao prova integralidade semantica e reduz confianca em enderecos derivados de metadados defeituosos.

Fontes: private-analysis/unins000.exe.decompiled.txt e .inventory.txt; unins000.raw-string-hits.txt usa offsets de arquivo. Busca legivel do executavel nao encontrou endpoint do fabricante; URL do manifesto e namespace XML. Rede via COM/indirecao/dados nao legiveis: UNKNOWN. Nenhum trafego foi observado.

### unins000.dat: estrutura validada integralmente

19.793 bytes. Parser reproduzivel parse_uninstall_log.py; resultado private-analysis/unins000.dat.parsed.json.

FUN_004b3418 le cabecalho 0x1c0 e verifica CRC32 sobre 0x1bc; FUN_004aa8ec implementa CRC com inicializacao/finalizacao invertidas. CRC do cabecalho 0x325c8664 confere. FUN_004b61bc escreve tamanho u32, complemento u32, CRC32 u32 e payload; FUN_004b6240 limita blocos a 4096. Cinco blocos de 4096/4096/4096/4096/2901 bytes: todos os complementos e CRCs conferem.

Stream logico 19.285 bytes; exatamente 101 registros conforme cabecalho. Registro: tipo u16, flags u32, tamanho u32, payload. Todos os limites chegaram ao fim sem residuos. FUN_004b3fc8 descreve campo serializado por tamanho imediato, 0xfd+u16, 0xfe+i32 ou terminador 0xff; tamanho negativo e bytes UTF-16. Todos os campos foram percorridos por tamanho, incluindo binarios identificados por digest. Validacao estrutural integral nao equivale a decompilacao do bytecode IFPS.

Cabecalho: AJAZZ AJ199 Gaming Mouse; AppId {ACAE738F-CF0F-426E-B48A-0BE006823AE4}. Registro 0 guarda metadados locais de maquina/usuario e diretorio instalado. Retidos no JSON privado; nao implicam coleta remota.

| Tipo | Quantidade | Interpretacao |
|---|---:|---|
| 0x10 | 1 | metadados iniciais |
| 0x20 | 1 | estado de script/instalacao com IFPS |
| 0x81 | 11 | registros de diretorios, incluindo duplicata |
| 0x82 | 86 | arquivos/atalhos |
| 0x86 | 1 | exclusao recursiva de chave HKLM |
| 0x11 | 1 | campo binario final 16 bytes; semantica exata UNKNOWN |

### Acoes AJ199 registradas

Registros 2-89 apontam para Program Files (x86)/AJAZZ/AJ199 Gaming Mouse: skins, skins/4001, skins/number, sc/en, Cfg.ini, OemDrv.exe, InitSetup.dll, uninstall.dll e appico.ico. Lista completa por indice, offset logico, flags e campos no JSON.

Registros 4 e 87: LocalAppData/JM03 e JM03/lang.ini. Registro 4 flags 0x2: dispatcher 0x004b4e74 usa 0x2 para diretorio, 0x4 para enumeracao, 0x8 para recursao; 0x4/0x8 estao desligadas. FUN_004ad230 chega a tentativa de remocao simples pelo callback de diretorio. Assim esse registro tenta remover JM03 vazio; lang.ini possui exclusao separada. Arquivos de perfil posteriores nao constam da lista e impediriam a remocao simples de JM03. Callbacks IFPS ainda podem produzir outros efeitos.

Registros 88-98: Menu Iniciar comum, Desktop e Startup do usuario, com pares .lnk/.pif AJAZZ AJ199 Gaming Mouse. Logo ha evidencia especifica de inicializacao automatica pelo atalho Startup. Sem entrada Run especifica do produto nos registros. Alvo registrado para limpeza nao prova que exista atualmente. Texto de script inclui Run on system start automatically.

Registro 99: tipo 0x86, flags 0x80000002, chave Software/Microsoft/Windows/CurrentVersion/Uninstall/{ACAE738F-CF0F-426E-B48A-0BE006823AE4}_is1. FUN_004b3b64 separa vista por bit 0x01000000 e mantem raiz 0x80000002 (HKLM). Dispatcher chama FUN_0047f978 para exclusao recursiva. Portanto a chave especifica HKLM esta resolvida. Nao ha registro 0x89 (valor isolado) nem 0x80 (Exec) neste log.

Campos de caminho serializados contem separadores duplicados; caminhos acima normalizados para leitura; texto literal e digests retidos no JSON.

### IFPS e limites remanescentes

Registro 1: primeiro campo binario 1434 bytes, assinatura IFPS, e outro binario 1090 bytes; diretorio instalado, diretorio de atalhos e idioma en. Nomes/constantes legiveis: SetupInit, dll:setup:files:InitSetup.dll, INITIALIZESETUP, FINDWINDOWBYWINDOWNAME, SENDMESSAGE, SLEEP, CURUNINSTALLSTEPCHANGED, INITIALIZEUNINSTALLPROGRESSFORM, SETINIINT, LangIndex, {localappdata}/JM03 e {localappdata}/JM03/lang.ini.

Essas ligacoes sao especificas do instalador; ordem, argumentos e condicoes presentes foram resolvidos pelo parser IFPS da segunda passagem: WM_CLOSE condicional seguido por Sleep1000. Ver capitulo IFPS; o binding original dos dois AfterInstall customizados continua ausente. Idioma en e estado registrado; nao certifica lang.ini atual. A rotina SetupInit da DLL demonstra limpeza, mas a condicao/argumentos efetivos do callback IFPS ainda precisam ser resolvidos.

Nenhuma instalacao, desinstalacao, exclusao, mudanca de registro, reinicio ou rede foi executada nesta analise. Helpers/DAT nao estabelecem formato HID, DPI, polling rate ou macros. Dados observados do log descrevem esta instalacao e nao todas as instalacoes possiveis. Acoes de arquivos/atalhos e chave HKLM foram resolvidas; todos os corpos IFPS presentes foram decodificados; o binding de instalacao dos dois exports AfterInstall permanece parcial.


## Bytecode IFPS integralmente decodificado

Escopo: nenhum bytecode, DLL, instalador ou desinstalador do fornecedor executado. Parser Python proprio apenas le bytes. Ghidra reutilizado exclusivamente pelos exports privados existentes; nenhum projeto compartilhado aberto. REA Evidence IDs e limite do provedor Ghidra 12.2 permanecem os descritos em HELPER_FINDINGS.md.

### Identidade, cobertura e reproducao

Fonte: inputs/unins000.dat, SHA-256 649ef6f4fa1cf2701125a2513d504dfa27457014f6c227b0d381828b7fe91d4a. Registro 1, tipo 0x20, flags 0x85030400. Primeiro payload IFPS inicia no offset logico 0xc8, fisico DAT 0x294; comprimento 1434 (0x59a), SHA-256 c808ea150ea668da579fc75cbe39a381be29a607cb271377f6b481bef2b82ac2. Todos estes bytes ficam no primeiro bloco, portanto offset fisico de qualquer byte IFPS = 0x294 + offset IFPS.

Executar `python AJ199_RE/decode_ifps.py` a partir de [analysis-workspace] reproduz private-analysis/ifps.decoded.json e ifps.disassembly.txt. O parser nao emula nem executa instrucoes. Contem assertions de limites, atributos ausentes, opcodes efetivamente usados, extensao final e consumo integral dos 1090 bytes de mensagens. O parser anterior valida CRCs e os 101 registros; este parser depende dessa estrutura ja validada.

Cabecalho: assinatura IFPS, build 23, 29 tipos, 13 procedimentos, 4 globais, main=0, ImportTableSize=0. Tabelas terminam em 0x25c; codigo ocupa 0x25c..0x598 inclusivo, seguido por byte 00 em 0x599. Todos os corpos foram decodificados integralmente. Os JSONs preservam instrucoes, bytes hex, offsets absolutos e relativos, tipos, declaracoes e saltos. Tipos 10/16/17/26 nesta tabela significam respectivamente S32/UnicodeString/AnsiString/BOOLEAN (os indices nao sao valores de BaseType). Globais G0/G1/G2 sao S32; G3 UnicodeString. G1 nunca e lida/escrita pelo bytecode decodificado.

Formato derivado do codigo primario RemObjects: [uPSRuntime.pas](https://github.com/remobjects/pascalscript/blob/master/Source/uPSRuntime.pas), LoadData/LoadTypes/LoadProcs/ReadVariable e RunScript; [uPSUtils.pas](https://github.com/remobjects/pascalscript/blob/master/Source/uPSUtils.pas), opcodes e BaseType. Copias textuais consultadas: private-analysis/uPSRuntime.reference.pas e uPSUtils.reference.pas. Upstream master e referencia de formato, nao prova da revisao exata incorporada pelo fornecedor. Todos os limites e opcodes presentes conferem neste artefato. Na referencia, cm_sf com DoNot=1 inverte o teste; cm_fg salta relativamente ao fim da propria instrucao.

### Procedimentos e resultados

| Indice | Nome | Corpo IFPS [inicio,fim) | Resultado estatico |
|---|---|---|---|
|0|!MAIN|0x25c..0x25d|return apenas|
|1|SetupInit externo|declaracao em 0xd0|dll:setup:files:InitSetup.dll, export SetupInit|
|2|InitializeSetup|0x25d..0x346|busca janela; fecha se encontrada; retorna true|
|3|FindWindowByWindowName|import em 0x125|busca pelo titulo literal|
|4|SendMessage|import em 0x143|argumentos resolvidos abaixo|
|5|Sleep|import em 0x159|1000 ms somente no ramo com janela|
|6|MyAfterInstall|0x346..0x393|SetupInit com caminho expandido JM03|
|7|ExpandConstant|import em 0x187|expansao de caminho|
|8|CurUninstallStepChanged|0x393..0x394|return apenas, ignora argumento|
|9|MyAfterInstall2|0x394..0x4bc|escreve idioma em INI|
|10|ActiveLanguage|import em 0x1ed|idioma ativo|
|11|SetIniInt|import em 0x202|OPT/LangIndex|
|12|InitializeUninstallProgressForm|0x4bc..0x599|busca janela; fecha se encontrada|

Os offsets de import na tabela indicam inicio do registro, incluindo flags. Declaracoes externas completas hex e registros exatos no JSON; a declaracao da DLL tem 45 bytes: `dll:setup:files:InitSetup.dll\0SetupInit\0` seguido por 03 01 00 01 00. O nome e locator da DLL sao literais; sem atribuir significado adicional nao verificado aos cinco bytes de convencao/assinatura.

#### Fechamento da janela

InitializeSetup procura a janela pelo titulo exato. Se a encontra, envia WM_CLOSE de forma sincrona e depois espera1000ms; se nao encontra, pula ambas as operacoes. Retorna verdadeiro nos dois casos. A descricao e comportamental, sem codigo recuperado.

Offsets IFPS: call FindWindow 0x28f; compare <>0 0x29b; flag invertida 0x2b0; salto 0x2b8 para 0x339 quando janela=0; argumentos empilhados de tras para frente (0,0,16,G0), call SendMessage 0x314; Sleep 0x333; retorno true 0x339. Assim 16 decimal = 0x10, mensagem Win32 WM_CLOSE. O resultado SendMessage e descartado. Nao ha verificacao de que o processo morreu apos a pausa, nem PID/caminho/identidade da janela alem do titulo.

InitializeUninstallProgressForm repete a mesma logica, sem retorno booleano: call FindWindow 0x4ee; compare 0x4fa; flag 0x50f; salto 0x517 para return 0x598; call SendMessage 0x573; Sleep 0x592. Nao envia mensagem e nao dorme se a busca retorna zero. A pausa e posterior ao retorno da chamada sincrona SendMessage; nao e um timeout imposto a ela.

#### Limpeza e idioma: corpos resolvidos, binding de instalacao ausente

MyAfterInstall: literal em 0x355; ExpandConstant em 0x37d; SetupInit em 0x38a. Equivale a `SetupInit(ExpandConstant('{localappdata}\JM03'))`; retorno da DLL descartado. Com a analise previa de InitSetup.dll!SetupInit (0x10001080), isto identifica o argumento efetivo da limpeza recursiva dos conteudos de JM03, preservando o diretorio inicial. O corpo nao possui teste previo nem ramo sobre resultado.

MyAfterInstall2 inicializa G2=0 (0x394), obtem ActiveLanguage em G3 (0x3a9), compara com 'en' (0x3b4) e reatribui 0 se igual (0x3d8); depois compara 'sc' (0x3ec) e atribui 1 se igual (0x410). Qualquer outro idioma fica 0. ExpandConstant em 0x45f resolve `{localappdata}\JM03\lang.ini`; call SetIniInt em 0x4b0 recebe, na ordem da API, ('OPT','LangIndex',G2,caminho). Booleano de sucesso e descartado. Nao ha criacao explicita de diretorio neste corpo.

Os nomes MyAfterInstall/MyAfterInstall2 sao exports customizados; nenhum outro corpo IFPS os chama. O !MAIN vazio nao os chama. Sem entradas do instalador [Files]/AfterInstall ou o setup original, o DAT nao prova quando, quantas vezes, em qual ordem, nem se esses dois exports sao invocados durante instalacao. Por isso nao concluir automaticamente que toda instalacao limpa perfis e depois recria lang.ini. Os corpos e argumentos estao resolvidos; seu binding permanece desconhecido. Nenhum deles e chamado diretamente pelos callbacks de desinstalacao presentes neste script.

### Ordem de desinstalacao corroborada pelo Ghidra

Fonte: private-analysis/unins000.exe.decompiled.txt, FUN_004f41ec e FUN_004f4b10; fluxo principal ao redor das linhas 166940..167050.

Na rota de desinstalacao exibida: tentativa opcional de InitializeUninstall (nao exportado por este IFPS), confirmacao quando aplicavel, CurUninstallStepChanged(0), verificacoes do log, FUN_004f41ec => InitializeUninstallProgressForm, CurUninstallStepChanged(1), FUN_004b4e74 para remover registros, verificacao de reinicio, fechamento da UI, CurUninstallStepChanged(2), tratamento de mensagens/reinicio e CurUninstallStepChanged(3). FUN_004f4b10 mascara valor com 0x7f antes de repassar; os bytes superiores espurios dos parametros CONCAT31 no pseudocodigo nao mudam esses valores. O dispatcher verifica o objeto de script nao nulo.

FUN_004f41ec chama InitializeUninstallProgressForm antes da condicao DAT_00502f48 que decide exibir a UI. Portanto o corpo de fechamento da janela nao depende nessa funcao da exibicao visivel do formulario. CurUninstallStepChanged e vazio para todos os passos. UninstallNeedRestart nao e exportado no IFPS. Nenhuma rotina de limpeza SetupInit, escrita de idioma ou novo reinicio e adicionada pelos callbacks de desinstalacao deste blob.

### Os 1090 bytes: tabela de mensagens, integralmente resolvida

Campo 6 inicia no offset logico 0x7ac, fisico DAT 0x978. Conteudo: u32=13, seguido por 13 pares de strings (u32 comprimento em caracteres, UTF-16LE). Parser consumiu exatamente 1090 bytes sem sobra. Chaves: NameAndVersion, AdditionalIcons, CreateDesktopIcon, CreateQuickLaunchIcon, ProgramOnTheWeb, UninstallProgram, LaunchProgram, AssocFileExtension, AssocingFileExtension, MyAppVerName, MyAppName, RunConfig, Auto. Valores completos no JSON. Auto contem espaco inicial seguido por Run on system start automatically. Trata-se de texto de interface, sem acao ou bytecode demonstrado. Nao usar a presenca de ProgramOnTheWeb para inferir endpoint.

### Limites finais

Fechados: formato/consumo IFPS; todos os imports e corpos presentes; condicoes e argumentos de SendMessage/Sleep; argumento SetupInit; regras de idioma/INI; ausencia de efeitos no callback de passos; ordem de callbacks no engine exportado; classificacao integral do segundo binario como mensagens. Nao resolvidos pelo material: binding/ordem/reachabilidade dos dois exports customizados na instalacao original, efeito efetivamente ocorrido no computador, sucesso de exclusoes/escrita e morte do processo. Nenhum comportamento de rede, HID ou firmware pode ser inferido destes callbacks.


## Inventário integral de identidade

Cada arquivo foi lido integralmente para SHA-256; isso não significa que cada payload gráfico tenha sido interpretado semanticamente. Todos os caminhos são relativos à instalação original. Nenhum asset ou código original é incluído nesta especificação.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `appico.ico` | 25214 | `5934620bce1660b688d3d308dfeffaeeee6dd6e8da36de2fdaada0ca81ed49ac` |
| `Cfg.ini` | 1532 | `40dfc065d77175a1eaee6e6704852ae10fdd1e1b681175a135a7b3b625dd7e8d` |
| `en/text.xml` | 16526 | `4795779cbcc8a97805dfcc4a7a8a8b2d6456601287f9cafac3a1d0ee5be2773f` |
| `InitSetup.dll` | 56320 | `72f5cfe575253eaff31e27ce8f70b4caaa079d2c42a4130515eecf7f0967115d` |
| `OemDrv.exe` | 2211840 | `ac9ca7cf9e072322589324f3027a65b681ccee8b44bf7c74b288627bf9d58846` |
| `sc/text.xml` | 12874 | `42b0b08239daaf8fad66ce03e84da3875cf65299a35a51efd7a214b04750dd8a` |
| `skins/4001/mouse_led.png` | 35481 | `ff895e7980979ea272a456e53ac765774e2043e6f2759073bb52f7375567bc25` |
| `skins/4001/mouse_nr.png` | 30232 | `6fd8f8a17d247869f1ca0bf433ef38ea47a119a027b57fdd12b454ec1bb297fd` |
| `skins/adv_nr.png` | 177973 | `d9d2df51b201d881e1b31f2e4ea8ada45f7a2ae38b2da6ece411708ef0e80082` |
| `skins/bar_nr.png` | 2924 | `454c8acdcae8b6ea52c9f5a824dc799ca7f579a989f3281f4922d735daaeba11` |
| `skins/bar_ov.png` | 2904 | `b884f520f9c7860a4c7b9c0e856aa10e4146cf9bc12bb7a47f9a40bf22e3f20c` |
| `skins/button2_nr.png` | 3081 | `734ad1cc57c7594a24581878e849a7826ae2a5f5e784652566d9e4739c5b24de` |
| `skins/button_nr.png` | 2957 | `6ef245438b1dd8fba83a0b469c197fea8d2db09f4f22854f8882f42453b5cb35` |
| `skins/check_dn.png` | 2931 | `8b020b0156c8515ad3faeb79481cab9ef0b1c239bf681ae81d5eeea09a4d786a` |
| `skins/check_nr.png` | 2821 | `cefd49030686a8e9364a266901f8285a6954f135f49c144369fff762b026f844` |
| `skins/color.png` | 19782 | `7fedde9030d655d281554af548c5d7b0889233b6c23d0a7ff912e9127d51bddf` |
| `skins/combo2_nr.png` | 2957 | `5420eab558e0ae0eff88c8094b711339c2e37d55f44c031b958b219e02bbfc45` |
| `skins/combo3_nr.png` | 2957 | `193cc7a8cfe4b4dd0255c4e29f1488eadfb4c6c5a133f79325fb63b74875ca46` |
| `skins/combo_nr.png` | 2969 | `a6ef5e3b818ac3d5fea177c3d6ac7b6794decc6c85a81ac07b75a5d898342975` |
| `skins/dpibar_nr.png` | 2911 | `e544e1b327cd4ce50d3ccab5c24eea5fe129259a09e3616a8ffe38b9d1d0e031` |
| `skins/dpibar_ov.png` | 2872 | `dd65f424c33dd647b217ededdd911862c65779e89a0cb59f3830e1c7e33e18ee` |
| `skins/exit_nr.png` | 3604 | `9de46c802c8d4d4ca6136ebd4744de5b50c7895a811c3f0550d2d76ef746d0b2` |
| `skins/help_nr.png` | 3770 | `5b47a7f4e31acd4cf3c6e281a852720544ce5253d7c897e416a871407f159bad` |
| `skins/key_nr.png` | 302915 | `e323474b7a7371ac2b81c6363a4738eee677018b981718fa0e08af0de86d0e9a` |
| `skins/key_time.png` | 3070 | `eb15cf3bbf72eef52c0b011aaca84a73ea845b143aebff3f7331ed38df959bfe` |
| `skins/led_nr.png` | 287971 | `4073d6927abab1b3803f14f54a3feaaca706d553bc2e6b59a97401b5e92911f8` |
| `skins/longbar_nr.png` | 2950 | `253811f38f2fe8f858362467a49fc25e24b9ff56a107e133e1b34f321a4271da` |
| `skins/longbar_ov.png` | 2928 | `440bbfadf24d5ff707c39ed34b459a50c00c703ffef65c722892a7a4cb35219f` |
| `skins/mac_d.png` | 2893 | `05f81f8a0fe1d06f26ea081140761f1e01d8029de0380167851f6d748e22affc` |
| `skins/mac_m.png` | 247 | `770c8d0a859833a3d584f9cd5cf514c8c56cfd5eeee36ee7806ab80242f87197` |
| `skins/mac_t.png` | 2945 | `22a6dec9f4fe9ec201673ec6812f50970803c9cb2394aebd28ec2cda54edf59c` |
| `skins/mac_u.png` | 2895 | `6e86808e07d52a8923a24c1920d959eaf8e3cd71122cc98f8362fc2faa0d4d99` |
| `skins/macro_nr.png` | 129400 | `91acf4cd432eaa5144d7705c1b966efb22c70b2e86561bbe3c0d0bcab9dd4ede` |
| `skins/mak.skn` | 520 | `1082c42654daa8c15acdd255a6abfff15226e57402a448cd1c9847ed8ffc9069` |
| `skins/menu_nr.png` | 175 | `b1e1fde55eaeed87d83d42abefc23a806625adb26f798013709a0649856d598d` |
| `skins/menu_ov.png` | 179 | `3469d598d2c7458a4d750380ad3d41afcfe6d357560cac973666686ceadb30d8` |
| `skins/menusub_nr.png` | 454 | `89a7730aba73c8f246df2d415b73c08bb9ede20ea5094dfeab12441cd0a35695` |
| `skins/menusub_ov.png` | 435 | `3ceeffbf950cc35d181be6230725f81f5e1d4598b22ac72aeae44cdae25a7280` |
| `skins/min_nr.png` | 3039 | `ec17a8056236f427fcc98493c82988ff88bfbb86d6e4f508cb100687c7342bf8` |
| `skins/msg.png` | 3831 | `c84471d6294457527a389dc3e59c302155a1de657f08be56290cb34767c85f32` |
| `skins/msg2_nr.png` | 22718 | `af9809ab88af8613e73b0a03a78e82543bbc1db1ffb42592bb89b175c07ed297` |
| `skins/msg_nr.png` | 3148 | `e26c49e182f09de23300bd5de50ec67fa28a073f8392723a556b5bbe72f130e4` |
| `skins/navi1_dn.png` | 4229 | `d7fe2fc8ac8dce1e6fe89ceea975b381d915934e3c28450b182245411c4b4761` |
| `skins/navi1_nr.png` | 4648 | `2bff51cfee4d43336425bde166edf7c63efb5995e8918aa6b712f59505060f77` |
| `skins/navi2_dn.png` | 3671 | `f4ff8be5d256eac3e6b0eae201a0ebea0ecd993e571e2eedc89671dfdbf68d1a` |
| `skins/navi2_nr.png` | 3830 | `b4cc79ce688e03f6923e63db562f879afbcdbc093e539596048e1dafb39b511e` |
| `skins/navi3_dn.png` | 3371 | `5732c9146f2f9e4596c92eb3eb48e79f2884dd936772fb6460ea33439870e3fb` |
| `skins/navi3_nr.png` | 3427 | `ce5738d5768896cfa375f9d290313b85c0ad2d0521373b2cd579647b96ad79fb` |
| `skins/navi4_dn.png` | 3713 | `eb0855ddb53c9f0858770d14295ccc04a3e57cd8516fca345604f3afa31bad8e` |
| `skins/navi4_nr.png` | 3895 | `165528eb08f2043e2ada0ae8da9f30fa4b1e0ba2dce7e20125ec741ff49a76b8` |
| `skins/notify.png` | 3927 | `1f05be9654b07ca3b20054fa7ee4f2c195f80c3fcadf5a8a29b7cbc5043dd9e4` |
| `skins/number/number1.png` | 4017 | `850ffb493f2c2062b25b1acf271640df78487752d5fb0e9dcd946aad340ee53a` |
| `skins/number/number10.png` | 4095 | `6b492eddd65f89a604d8b9217bcfeb19f8beb74763534dd0e9ab24534a7aced1` |
| `skins/number/number11.png` | 4027 | `e22a8e66e1bec322cdcda4781c7b3be6ee1d038a16610f1036b77a3f4a98225e` |
| `skins/number/number12.png` | 4143 | `d22ea3be050cdd9bb4fe0e20be82b683d86ac540e2ff9db8e6ce9c5659f06826` |
| `skins/number/number2.png` | 4107 | `2b8a07a85e0b404845522fc6010f48512da4e1a2c5088eceb584551139946b93` |
| `skins/number/number3.png` | 4095 | `04dbde81ae272e0f90fe97bb6583fe5df1a7e40a0d86f3912ece54189c23f861` |
| `skins/number/number4.png` | 4098 | `362a53a0de08bc70e6beb79c635d243cdcbe3d0a906860f3fb73cb904c98640f` |
| `skins/number/number5.png` | 4097 | `76fc4cf35832634e998d233bc90c38705b266d4c62ed4f0b66113fa5ec86b36d` |
| `skins/number/number6.png` | 4106 | `bd69d96899a9e37ad735ad2d012f3faeb0f5cf597f040abdef3e0e3682e88b37` |
| `skins/number/number7.png` | 4048 | `20b0ad8ccca3aa064e7b9d9792fac46888900bb0b8e15b814bde099127b41f89` |
| `skins/number/number8.png` | 4107 | `41f652b0ad5ff889b715322a0625ff76832c3ab5c6aefa0ef8f0f7ff7baea6f1` |
| `skins/number/number9.png` | 4086 | `f94d0b77a5ac333bc9143bf17b11d78d2b88757b2828ee1b5de7c4e85f2185ab` |
| `skins/power1.png` | 2915 | `1abbda60d902710b2cd1464eba532623550410c2443c913fd83cfbe94fbe5a91` |
| `skins/power2.png` | 2976 | `b85c36694672c4aee74ce5fcf9c56a90a0e67a193f6ecb63e9d64bd8cb537883` |
| `skins/power3.png` | 2896 | `7ca359c5e75b86da5e933189396b227a1ca2d479c0ff4682f4396bcb7dbabb02` |
| `skins/power4.png` | 2884 | `478db337540c5c8518d489939aaa245f1e15890459a19c186473bcb5b5d92858` |
| `skins/power_charging.png` | 3541 | `f25c888dbb6af5ef729e09cb41119fadb8098b3e9962fbe5266d229d305f87c2` |
| `skins/progress_nr.png` | 837 | `6de0e8d7e9521a7e84fb910311fd4510c443d8933620e5e760909d365eea051a` |
| `skins/progress_ov.png` | 867 | `a3f1bea7f8f71fc2ee2ad23e981c4320134eaee4c2cea3af8ba24ebb0c87e3e7` |
| `skins/radio_dn.png` | 3010 | `5bc2a2367b2edf890148af4ffc006078e1566bd81d91bf63bd40aea5014c1218` |
| `skins/radio_nr.png` | 2947 | `18d9a39368561b984a27eadee7795b97ec77786e392975bae6daf80201c52198` |
| `skins/reset_nr.png` | 3090 | `afecf78aa9a5b255a0542a7f6b7fa085f32e778f9e3d5e9d26bbf4e74ca8a178` |
| `skins/slider.png` | 2889 | `8dfe8261a9dba729a3627c2e2b57954902d4e376f2e5272be66c8331db8dae2e` |
| `skins/slider1.png` | 2883 | `e1a54071ba7e1d0623b5d3adabcfddbb293474110b11ba509788071e7310ae83` |
| `skins/slider2.png` | 2874 | `9fe219fa55f8fd4085e74eb5c593f8533b21acd29ad023ceb4e254612d9a540d` |
| `unins000.dat` | 19793 | `649ef6f4fa1cf2701125a2513d504dfa27457014f6c227b0d381828b7fe91d4a` |
| `unins000.exe` | 1202637 | `c7b7ff4119af4036ca995b3862fecfd482a3215f535467bb9e84010a5393bbe5` |
| `uninstall.dll` | 32768 | `64c8831379fed7f9ab3221b44cb6dba8bf3a5e45cd9308f4c8ae5cf2c7c2b536` |

## Cobertura Ghidra e limites dos resultados

| Binário | Funções reconhecidas | Pseudocódigo retornado | Observação |
|---|---:|---:|---|
| OemDrv.exe | 12490 | 12490 | Aviso0042B6E0; convenções de chamada/pilha imperfeitas |
| InitSetup.dll | 234 | 234 | Metadados e fluxo analisados estaticamente |
| uninstall.dll | 25 | 25 | Metadados e fluxo analisados estaticamente |
| unins000.exe | 4355 | 4355 | Avisos PE relocation/TLS/export |

Total do export inicial: 17104 funções reconhecidas. A segunda passagem recuperou mais seis entradas que estavam fora desse inventário, incluindo0043DC20/0043EBC0/0043B970; não se transformou a contagem inicial em garantia de integralidade. A contagem inclui bibliotecas/CRT/MFC e nomes automáticos; não significa revisão semântica manual de cada função nem ausência de código não reconhecido. A função0042B6E0 gerou aviso de leitura de memória não mapeada, apesar de retornar pseudocódigo. Não há PDB do fornecedor. O processo preexistente foi instrumentado por REA/Frida; foram feitas navegação de UI e22 consultas explícitas de leitura, com respostas capturadas. O original também enviou seus comandos normais de status/bateria. Não houve escrita EEPROM07, reset, firmware, instalação, desinstalação ou reinício do alvo.

## O que esta entrega permite e o que permanece UNKNOWN

A especificação documenta uma base de implementação independente para Linux, com formatos e transporte detalhados, inclusive22 pares reais de leitura/ACK. Não contém código recuperado do fornecedor, imagens reutilizáveis, traduções integrais nem um clone implementado. Permanecem UNKNOWN: efeitos físicos de todas as escritas e persistência após desligar; interpretação física de alguns parâmetros; reprodução de macros; rádio e bootloader; firmware não fornecido; binding dos callbacks AfterInstall no instalador original ausente; geometria de todos os estados e comportamento de todos os erros. A execução nativa Linux exige implementação e uma matriz de testes; nenhuma análise de binários Windows prova funcionamento em literalmente todas as distribuições, kernels, arquiteturas e compositores. Estas dependências não são sanadas apenas por trocar ou repetir o decompilador.
