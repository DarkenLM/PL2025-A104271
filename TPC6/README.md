# TPC 5

**Titulo:** Intepretador de Expressões Matemáticas Simples  
**Data:**  2025-03-19  
**Autor:** Rafael Santos Fernandes  
**Número:** A104271  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
### Enunciado
Criar um analisador sintático recursivo descendente capaz de processar expressões matemáticas simples. Adicionalmente, o analisador deverá calcular o valor exato da expressão, de acordo com a ordem de operações.  
- Exemplos:
  - `5 + 3 + 2` (= 10)
  - `2 + 7 - 5 * 3` (= -6)

### Resolução
Para a resolução deste TPC, comecei por examinar o enunciado e retirar as seguintes conclusões:
1. As operações de exemplo fazem uso dos símbolos adição (`+`), subtração (`-`) e multiplicação (`*`), cujos significados correspondem aos dos seus símbolos matemáticos.
2. A ordem de operações assumida como PEMDAS, excluíndo os exponentes, que não existem nestas operações.
3. Por completude, decidi adicionar o símbolo `/` para a divisão, e parênteses para promoção explícita da prioridade.
4. O símbolo `-` foi, adicionalmente, utilizado para a operação unária do simétrico de uma expressão.

Decidi então tomar as seguintes decisões acerca do design da aplicação:
1. Decidir separar a funcionalidade da interpretação das expressões em Análise Léxica, Análise Semântica e Execução.
2. O Analisador Léxico transforma o texto-fonte numa lista de tokens, que são passados ao Analisador Sintático, que transforma a lista de tokens numa AST, que é passada ao Executor, que interpreta a AST e a reduz a um único valor.
3. O Analisador Sintático gera uma AST que representa uma única expressão, que é constituída por todo o input.
4. Para a ordem de operações, decidi utilizar o Algoritmo de Pratt.

#### Análise Lexical
A primeira fase começa por ler o input caratér a caráter e selecionar um candidato a partir de uma lista de tokens, ou retorna ou erro caso nenhum candidato aceite o caratére na posição atual. O candidato analisa então o código-fonte caráter a caráter a partir da posição atual do analisador e cria um token a partir de uma sequência de caráteres, que é passado como elemento de um gerador para a próxima fase, ou lança um erro lexical caso a sequência não seja válida para o token em questão. Entre cada iteração do ciclo, o espaço em branco é lido e ignorado.

#### Análise Sintátca
A segunda fase consome os elementos do gerador proveniente do analisador lexical e tenta construír um nodo de expressão. Um nodo de expressão é uma AST constituída por um operador e um ou dois operandos.  
O analisador começa por consumir o token na posição atual e determinar o seu tipo: operador ou operando. Caso seja um operando, esse token é transformado num nodo literal e selecionado para o *Left-Hand Side (LHS)*. Caso seja um operador, a expressão é classificada como uma expressão unária, não possuíndo *LHS*, passando diretamente para o procesamento do *Right-Hand Side (RHS)*. Adicionalmente, caso o operador seja um parênteses a abrir (correspondente ao caráter `(`), a expressão é classíficada como expressão nulária, e é processada recursivamente uma nova expressão com prioridade absoluta até encontrar um parênteses a fechar (correspondente ao caráter `)`), ou retorna um erro se a expressão nunca é fechada.  
De seguida, o analisador segue o [Algoritmo de Pratt](https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html) para avaliar a ordem de operadores na expressão, seguindo os passos:
- Enquanto existirem operadores não processados na expressão:
  1. Ler o operador e determinar os seus *binding powers*.
  2. Caso o *LEft Denotation binding power (LED)* seja inferior ao *Minimum Binding Power (MBP)*, parar a análise e retornar o controlo para a iteração recursiva anterior.
  3. Iniciar uma nova iteração recursiva para processar o *RHS* da expressão a partir da posição atual, tomando o novo *MBP* o valor do *RIght Denotation binding power (RID)* do operador.
  4. Substituir o valor do acumulador por um nodo de expressão contendo o aculumador atual como *LHS*, o operador, e o *RHS* processado no ponto anterior.
  5. Retorar a **5.**, continuando a processar a expressão a partir da posição atual com o *MBP* possuíndo o valor inicial da sua iteração.

A ordem dos operadores é determinada através de um dicionário contendo como chave o identificador do operator e como valor um triplo (*NUD*, *LED*, *RID*):
  - ***NU****ll* ***D****enotation (NUD)* é o *binding power* do operador quando o mesmo é classificado como operador unário prefixo, utilizado como valor para o *MBP* para o processamento do *RHS* da operação.
  - ***LE****ft* ***D****enotation (LED)* é o *binding power* do operador quando o mesmo se encontra á esquerda de uma dada posição. Numa dada iteração, caso o *LED* seja igual ou superior ao *MBP*, o operador possuí prioridade sobre um outro operador nessa iteração, sendo essa operação acumulada com a seguinte antes de retornar o controlo á iteração anterior, que ocorre quando o *LED* é inferior ao *MBP*.
  - ***RI****ght* ***D****enotation (RID)* é o *binding power* do operador quando o mesmo se encontra numa dada posição, utilizado como novo valor para o *MBP* no processamento do *RHS* de uma expressão em cada nova iteração recursiva.

#### Execução
A terceira fase analisa a expressão retornada pelo analisador sintático e processa a AST da expressão através de uma exploração *Depth-First, Left-to-Right*, avaliando o valor de cada operação e passando o seu valor á sua operação pai, eventualmente reduzindo toda a AST a um único valor numérico.

### Resultados
O programa pode ser executado através do comando:
```
$ python3 main.py
```
Após executar o comando acima, uma expressão matemática deverá ser introduzida, e após a introdução de um *newline*, a expressão será avaliada e o seu valor retornado.

#### Exemplo
```
$ python3 main.py
> 1 + 2 - 2 * 3
= -3
> 
```
