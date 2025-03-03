# TPC 2

**Titulo:** Análise de um dataset de obras musicais  
**Data:**  2025-02-24  
**Autor:** Rafael Santos Fernandes  
**Número:** A104271  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
### Enunciado
[Ver ficheiro anexado](./tpc4.pdf)

### Resolução
Para a resolução deste TPC, comecei por examinar o enunciado e, mais especificamente, a *query* fornecida de exemplo, retirando as seguintes conclusões:
1. A *query* em questão assemelha-se bastante a uma *query* da linguagem de *query* de base de dados SPARQL. Tal foi confirmado posteriormente numa aula teórica.
2. Comentários são caracterizados por um um caráter `#`, seguido de qualquer sequência de caráteres até uma *newline* (`\n`). Comentários não têm significado sintático e podem ser ignorados a nível léxico.
3. Existem `3` *keywords*: `select`, `where` e `LIMIT`. Não existindo nenhuma indicação relacionadas á interpretação de *keywords*, decidi aceitar usos mistos de caratéres mínusculos e maiúsculos.
4. Variáveis são caracterizados por um caráter `?`, seguido de uma sequência de caráteres na classe `[a-zA-Z]`.
6. A linguagem possuí identificadores, que pode ser caracterizado por uma sequência de caráteres na classe `[a-zA-Z]`, aqui denominado identificador simples, ou por um denominador composto, caracterizado por dois identificadores simples separados por um caráter `:`.
7. A linguagem suporta literais de texto, caracterizados por uma sequência de caráteres delimitados por caráteres `"`.
8. Adicionalmente, os literais de texto podem possuír um modificador, caracterizado por um caráter `@`, seguido de uma sequência de caráteres na classe `[a-z]`.
9. A linguagem suporta literais numéricos, caracterizados por uma sequência de digitos.
10. A linguagem possuí blocos de *statements*, delimitados pelos caráteres `{` e `}`.
11. Cada *statement* é terminado por um caráter `.`, á excepção do último presente num dado bloco, sendo opcional a sua terminação.

#### Gramática (Backus-Naur Form)
A partir das conclusões descritas acima, derivei então uma gramática formal na forma Backus-Naur de forma a definir a linguagem antes da implementação do seu analisador léxico, representada de seguida.
```bnf
<QUERY>        ::= <SELECT_QUERY>
<SELECT_QUERY> ::= "select" <VARIABLES> <WHERE_CLAUSE> <LIMIT_CLAUSE>

<LIMIT_CLAUSE> ::= "LIMIT" <NUMBER>

<WHERE_CLAUSE>       ::= "where" <WHERE_BLOCK>
<WHERE_BLOCK>        ::= "{" <WHERE_BLOCK_BODY> "}"
<WHERE_BLOCK_BODY>   ::= <WHERE_BLOCK_STMT> | <WHERE_BLOCK_STMT> <WHERE_BLOCK_BODY>
<WHERE_BLOCK_STMT>   ::= <VARIABLE> <WHERE_BLOCK_TARGET> <WHERE_BLOCK_SOURCE>
<WHERE_BLOCK_TARGET> ::= <IDENTIFIER> | <PREFIXED_IDENTIFIER>
<WHERE_BLOCK_SOURCE> ::= <VARIABLE> | <PREFIXED_IDENTIFIER> | <EXTENDABLE_LITERAL>

<VARIABLES> ::= <VARIABLE> | <VARIABLE> <VARIABLES>
<VARIABLE>  ::= "?" <IDENTIFIER>

<EXTENDABLE_LITERAL> ::= <LITERAL> | <LITERAL> <LITERAL_MODIFIER>
<LITERAL_MODIFIER>   ::= "@" <IDENTIFIER>
<LITERAL>            ::= '"' <TEXT> '"'

<IDENTIFIER>          ::= <CHARACTER> | <CHARACTER> <IDENFITIFER>
<PREFIXED_IDENTIFIER> ::= <IDENTIFIER> ":" <IDENTIFIER>

; <WHITESPACE>                 ::= <WHITESPACE_CHARACTER> | <WHITESPACE_CHARACTER> <WHITESPACE>
; <WHITESPACE_CHARACTER>       ::= <NO_LF_WHITESPACE_CHARACTER> | <NEWLINE>
; <NO_LF_WHITESPACE_CHARACTER> ::= " " | "\t"
; <NEWLINE>                    ::= "\n"


<TEXT>      ::= <CHARACTER> | <CHARACTER> <TEXT>
<CHARACTER> ::= <DIGIT> | <SYMBOL> | <LETTER>
<NUMBER>    ::= <DIGIT> | <DIGIT> <NUMBER>

<DIGIT>     ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<SYMBOL>    ::= "|" | " " | "!" | "#" | "$" | "%" | "&" | "(" | ")" | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | ">" | "=" | "<" | "?" | "@" | "[" | "\\" | "]" | "^" | "_" | "`" | "{" | "}" | "~"
<LETTER>    ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" | "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"
```

#### Analisador Léxico
O analisador léxico contém um conjunto de `Token`s, compostos por um **predicado**, que determina se o token em questão é candidato ao processamento do código na posição atual e um **leitor**, que tenta gerar um token com uma secção do código-fonte a partir da posição atual. Antes e depois da leitura de cada token, todo o *whitespace*, com a excepção de *newlines*, é ignorado. Caso a um dado ponto o programa encontre um carátere para o qual nenhum construtor seja candidato ao processamento, é lançado um erro léxico (`LexicalError`).

### Resultados
O programa pode ser executado através do comando:
```
$ python3 lexer.py <name>.dbp 
```
Que irá processar o texto-fonte presente no ficheiro `<name>.dbp` e gerar um conjunto de tokens, sobre o qual apresentará a sua representação textual no `stdout`.
