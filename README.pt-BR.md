# FUN60 Pro - RGB ao vivo (experimental) - MonsGeek FUN60 Pro, ID de modelo 2304

> **EXPERIMENTAL. LEIA [docs/SAFETY.md](docs/SAFETY.md) (em inglês) ANTES DE FAZER QUALQUER COISA.**
> Este projeto modifica o firmware do teclado. Um erro pode deixar o teclado sem funcionar, e ninguém aqui pode prometer recuperação.
> **Situação: validado em hardware real pelo mantenedor, em um único teclado** (FUN60 Pro, modelo 2304, firmware V309).
> Não testado em nenhuma outra unidade, variante ou layout. O que foi e o que não foi coberto: [O que foi e o que não foi verificado](#o-que-foi-e-o-que-não-foi-verificado)
> e [docs/TEST_REPORTS.md](docs/TEST_REPORTS.md).

Trabalho não oficial para ter **iluminação por tecla ao vivo no SignalRGB** no **MonsGeek FUN60 Pro** (USB `3151:502D`, ID de modelo **2304**,
firmware **V309**). Parte da abordagem publicada para o FUN60 Ultra em
[sinsaintly/fun60-signalrgb-fix](https://github.com/sinsaintly/fun60-signalrgb-fix), adapta para o Pro e documenta como cada passo foi
descoberto, para que outras pessoas possam conferir, reaproveitar ou adaptar para outro modelo.
Mantido por [S4nril](https://github.com/S4nril).

Sem relação com a MonsGeek, Akko, Rongyuan ou SignalRGB. As marcas pertencem aos seus donos.

## Limitação conhecida: o driver da fabricante (v1) e a variante v2

A imagem validada em hardware ("v1") grava o marcador de modo ao vivo nos bytes 3-6 da identidade. Os bytes 3-4 fazem parte do ID de modelo de 32 bits
que o driver da fabricante lê (segundo as notas do projeto Ultra), então **com a v1 o driver da fabricante deixa de reconhecer o teclado**, e o que só
ele consegue mudar (camadas FN, pontos de atuação) não pode ser editado enquanto a v1 estiver instalada. O mesmo aconteceu no Ultra.
Uma segunda versão, a **v2**, grava o marcador depois da versão do firmware (bytes 9-12) e não mexe nos bytes do modelo. **O mantenedor relata que
com a v2 gravada o driver da fabricante reconhece o teclado** (um teclado). **A v2 é a versão recomendada;** a v1 fica como referência e para
quem quiser comparar as duas.
Feche também o SignalRGB enquanto usa o driver da fabricante: o plugin não tem passagem de controle, então os dois programas falariam com o teclado ao mesmo tempo.

## Por que é preciso alterar o firmware

Com o firmware original, o único jeito de definir cores por tecla é o *Apply* do driver da fabricante, e esse comando **grava na memória
permanente** do teclado (testado: as cores continuam depois de desconectar). Mandar quadros assim, várias vezes por segundo, seriam
várias gravações em flash. O projeto do Ultra resolveu isso com um patch pequeno que cria um caminho só em RAM. Este repositório
adapta esse patch para a imagem do Pro e o cerca de ferramentas que se recusam a fazer o que sabem ser inseguro.

## O que tem aqui

| Caminho | O que é |
|---|---|
| `tools/build_pro_patch.py` | Monta a imagem modificada **a partir da sua própria cópia do firmware original**: `pro` = v1 (12 bytes alterados + 282 acrescentados), `pro-v2` = v2 (marcador movido, veja acima). |
| `tools/fun60pro_flasher.py` | Gravador que segue o protocolo de atualização USB do driver. `plan` e `inspect` não gravam nada; `flash` exige `--arm` e uma frase digitada. |
| `plugin/MonsGeek_FUN60_Pro_LiveRGB.js` | Plugin do SignalRGB. Só transmite se o teclado provar que roda o firmware modificado. |
| `tests/` | Testes de simulação (gravador contra um bootloader falso, plugin contra um SignalRGB falso, emulação de CPU da imagem). |
| `docs/` | Como foi feito, protocolo, patch, mapa de teclas, guia de captura, segurança, modelo de relatório de testes (em inglês). |
| `firmware/` | **Vazia de propósito.** O firmware é código da fabricante e não é redistribuído. |

## Quais teclados

Somente um FUN60 Pro que responda à identificação com **modelo 2304** e **firmware 0x0309**. O driver da fabricante lista outros IDs de
FUN60 Pro (2305, 2463, 2464, 2505, 2600 e outros) que este projeto **não** analisou. Não grave esses arquivos neles. As ferramentas
conferem modelo e versão e param se não baterem. O mapa de teclas cobre só o layout ANSI de 61 teclas.

## Fluxo resumido

1. `py -3 -m pip install hidapi` e depois `py -3 tools/fun60pro_flasher.py inspect` (só leitura): confirme modelo 2304 / versão 0x0309.
2. Baixe o firmware original do seu teclado, veja [firmware/README.md](firmware/README.md).
3. `py -3 tools/build_pro_patch.py pro firmware/fw_2304.bin ID2304-V309-livepatch.bin` (v1, validada em um teclado, mas o driver da fabricante deixa de reconhecer o teclado), ou
   `py -3 tools/build_pro_patch.py pro-v2 firmware/fw_2304.bin ID2304-V309-livepatch-v2.bin` (v2, recomendada: o driver da fabricante continua funcionando; validada em um teclado)
4. Leia [docs/SAFETY.md](docs/SAFETY.md) e confirme que você tem um caminho de recuperação.
5. `py -3 tools/fun60pro_flasher.py plan <imagem>`, depois `flash <imagem>` (só verificações) e `flash <imagem> --arm` quando decidir gravar.
   Recomendado: ensaiar antes gravando a imagem **original** por cima da original.
6. Copie `plugin/MonsGeek_FUN60_Pro_LiveRGB.js` para `Documentos\WhirlwindFX\Plugins` (deixe só um plugin de FUN60 lá) e reinicie o SignalRGB.

## O que foi e o que não foi verificado

**Verificado por simulação, capturas USB e leitura de código**

* Formato dos quadros, checksums e páginas batem, byte a byte, com capturas USB do driver.
* O montador reproduz byte a byte a imagem publicada do projeto Ultra a partir do original do Ultra.
* Emulação de CPU: resposta de identidade, relatórios normais inalterados, quadros com flag 2 copiados só para a RAM.
* Lógica do gravador contra um bootloader simulado, incluindo recusas e falhas.
* Protocolo de atualização lido do código do driver; 22 das 61 teclas vistas em capturas, as outras 39 por contagem de colunas.

**Funcionou em hardware real** (um teclado, testado pelo mantenedor S4nril: FUN60 Pro, modelo 2304, firmware V309)

* O firmware modificado v1 foi aceito e roda no teclado.
* O firmware modificado v2 foi gravado, tudo funcionou como o mantenedor esperava e **o driver da fabricante reconhece o teclado** com ele.
* RGB por tecla ao vivo no SignalRGB com o plugin.

É uma amostra de um. O registro passo a passo (versões dos programas, gravação de ensaio, restauração, conferência de teclas) ainda precisa ser
escrito em [docs/TEST_REPORTS.md](docs/TEST_REPORTS.md).

**Ainda não relatado / não verificado**

* Detalhes da v2 ainda não registrados: a saída do `inspect` depois de gravar, a edição de camadas FN e pontos de atuação no driver, o RGB ao vivo com a v2 tecla por tecla e se as configurações salvas sobreviveram à gravação.
* Qualquer outro teclado: outros IDs de FUN60 Pro (2305, 2463, 2464, 2505, 2600 e outros), outras revisões, layouts ISO ou outros.
* As 39 teclas derivadas conferidas uma a uma, e a passagem pelas 61 teclas com a propriedade `Debug slot`.
* Restaurar a imagem original em hardware real e recuperar pelo modo bootloader (só existem testes em simulação; nenhum teste em hardware de nenhum dos dois foi relatado).
* Como o driver da fabricante se comporta com o marcador de modo ao vivo presente (ele deixou de reconhecer o Ultra até ser alterado).
* Efeitos de longo prazo: desgaste da flash e se há algo importante na flash logo depois do fim da imagem.

## Versões

Há dois esquemas de numeração: as versões do repositório (tags do git como `v2.0.0`) e as duas variantes de imagem de firmware (`v1`, `v2`). A versão 2.0.0 é a
primeira que consegue montar a imagem **v2**. Veja [CHANGELOG.md](CHANGELOG.md) (em inglês).

## Documentação (em inglês)

[docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) (o método completo) · [docs/PROTOCOL.md](docs/PROTOCOL.md) · [docs/PATCH.md](docs/PATCH.md) ·
[docs/KEYMAP.md](docs/KEYMAP.md) · [docs/CAPTURE_GUIDE.md](docs/CAPTURE_GUIDE.md) · [docs/SAFETY.md](docs/SAFETY.md) · [docs/RECOVERY.md](docs/RECOVERY.md) (recuperação, configurações e calibração) ·
[docs/TESTING.md](docs/TESTING.md) · [docs/TEST_REPORTS.md](docs/TEST_REPORTS.md)

## Origem

A análise e o código foram produzidos com ajuda de um assistente de IA (Claude), a partir de capturas USB, do JavaScript público do
driver da fabricante, das imagens de firmware e dos arquivos públicos do projeto Ultra. Trate tudo como não revisado até ler você mesmo;
os testes existem para você conferir as afirmações. Depois, o mantenedor validou o
resultado em um teclado real (veja a situação acima).

## Licença

MIT para o código e a documentação originais, veja [LICENSE](LICENSE). A abordagem e a pequena rotina em código de máquina acrescentada
pelo patch vêm do projeto FUN60 Ultra citado acima; veja [docs/PATCH.md](docs/PATCH.md). O firmware da fabricante não está incluído.
