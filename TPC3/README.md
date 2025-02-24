# TPC 2

**Titulo:** Análise de um dataset de obras musicais  
**Data:**  2025-02-11  
**Autor:** Rafael Santos Fernandes  
**Número:** A104271  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
### Enunciado
[Ver ficheiro anexado](./tpc3.pdf)

### Resolução
Para a resolução deste TPC, comecei por examinar o enunciado e comparar com o meu conhecimento prévio sobre a especificação da linguagem Markdown, retirando as seguintes conclusões:
1. Os títulos são caracterizados por um ou mais caracteres `#`, seguidos de elementos de texto (regular, itálico, negrito), seguidos de uma newline.
2. As listas de elementos são caracteriadas por múltiplas linhas, que por sua vez são caracterizadas por um ou mais dígitos, seguidos de um ponto, seguidos de elementos de texto (regular, itálico, negrito), seguidos de uma newline.
3. Texto em itálico é caracterizado por um marcador de atributo de texto (`*`), seguido por texto regular, seguido por um outro marcador de atributo de texto.
4. Texto em negrito é caracterizado por um marcador de atributo de texto (`**`), seguido por texto regular, seguido por um outro marcador de atributo de texto.
5. Texto em negrito e itálico é caracterizado por um marcador de atributo de texto (`***`), seguido por texto regular, seguido por um outro marcador de atributo de texto.
6. Links são caracterizados por um caractere `[`, seguido por texto regular, seguindo pelos caracteres `](`, seguido por mais texto regular, seguido por um caractere `)`.
7. Imagens são caracterizadas de igual modo aos links, prefixadas por um caractere `!`.

Os pontos **1** e **2** em particular levaram á decisão de interpretar as newlines como tokens, de modo a impedir que os mesmos consumam tokens de texto pertencentes a linhas posteriores erroneamente.

Para a resolução, decidi criar um compilador de três fases (Análise Sintática, Análise Semântica e Geração de Código).

#### Análise Sintática
A primeira fase analisa o código-fonte caractere a caractere e, enquanto nenhum predicado do conjunto de tokens de primeira ordem aceitar o caractere na posição atual, adiciona-os a um buffer. Após um predicado aceitar o caractere, e imediatamente antes do seu processamento, o buffer é convertido num `LiteralToken`, e o token correspondente ao predicado tenta processar o caractere. Caso não consiga processar esse caractere, o token passa o controlo para o próximo token na sequência, que repete o mesmo processo.

O predicado de cada token é uma função que aceita como argumentos a stream de caracteres atual, o último token processado (ou `None` se nenhum token ainda foi procesado), e o buffer atual, e retorna um valor booleano que representa se o caractere na posição atual é candidado ao token associado.

#### Análise Semântica
A segunda fase analisa a stream de tokens resultante da fase anterior e lê a mesma token a token, com a possibilidade de lookbehind e lookahead. Para cada token, e para cada nodo em sequência do conjunto de nodos de primeira ordem, é executado o seu predicado. Caso o predicado aceite o token, o nodo associado tentará processar uma subsequência de tokens a partir da posição atual. Caso falhe, ou se o predicado não aceite o token, será passado o controlo para o próximo nodo na sequência. Caso nenhum nodo aceite o token na posição atual, um erro será lançado.

O predicado de cada nodo é uma função que aceita como argumento a stream de nodos atual e retorna retorna um valor booleano que representa se o token na posição atual é candidado ao nodo associado.

#### Geração de Código
A terceira fase analisa a stream de nodos resultante da fase anterior e lê a mesma nodo a nodo sequencialmente. Para cada nodo, e para cada transformador de um conjunto, é executado o seu predicado. Caso o predicado aceite o nodo, o transformador associado transformará o nodo na posição atual. Caso o predicado não aceite o nodo, será passado o controlo para o próximo transformador na sequência. Caso nenhum nodo aceite o token na posição atual, um erro será lançado.

O predicado de cada transformador é uma função que aceita como argumento o nodo na posição atual e retorna retorna um valor booleano que representa se o nodo em questão é candidado ao nodo associado.

### Resultados
O programa pode ser executado através do comando:
```
$ python3 markdown.py <name>.md 
```
Que irá gerar um ficheiro `<name>.html` com o código HTML gerado a partir do ficheiro `<name>.md`.

O código foi testado utilizando o ficheiro [`test.md`](./test.md), que resultou no ficheiro [`test.html`](./test.html).
