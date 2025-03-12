# TPC 5

**Titulo:** Máquina de Vending  
**Data:**  2025-03-08  
**Autor:** Rafael Santos Fernandes  
**Número:** A104271  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
### Enunciado
[Ver ficheiro anexado](./tpc5_maq_vending.pdf)

### Resolução
Para a resolução deste TPC, comecei por examinar o enunciado e retirar as seguintes conclusões:
1. O stock está definido através da estrutura `{ cod: string, nome: string, quant: int, preco: float }[]`
2. O stock existe num ficheiro JSON, que é atualizado no fim da execução do programa de modo a persistir os dados entre execuções.
3. Um banner é exíbido no início de cada execução da máquina, contendo a data atual.
4. O símbolo `>> ` é exibido de forma a demonstrar que o utilizador pode executar um comando.
5. O output normal da máquina é acompanhado do prefixo `maq:`.
6. Os comandos são construídos por uma string de caráteres alfabéticos, seguidos por zero ou mais argumentos, separados de maneira diferente por cada comando.

Decidi então tomar as seguintes decisões acerca do design da aplicação:
1. Os **COMANDOS** são interpretados sem sensibilidade de capitalização, por conveniência.
2. Comandos que utilizem um símbolo de término de sequência (ex.: `.` no comando **MOEDA**) são tolerantes á sua omissão, interpretando todo o input, ou terminam o processamento do input imediatamente após receber o símbolo.
3. Cada comando pode definir uma lista de *aliases*, que interpretam o comando do mesmo modo do nome principal, substituíndo o nome do comando pelo seu *alias*.
4. Cada comando pode optar por se esconder da lista de comandos e condicionalmente negar a sua execução.
5. O processamento do input de cada comando, após o seu identificador, é deferido a cada um, que pode utilizar qualquer método de processamento léxico e sintático.
6. O processamento léxico e sintático ocorrem numa fase diferente do processamento semântico e interpretação, que permite uma melhor transmissão do estado de erro ao utilizador. Esta abordagem permite também a introdução de comandos de execução condicional.

Baseado nas decisões supramencionadas, decidi então criar um interpretador de duas fases (Análise e Execução).

#### Análise
A primeira fase começa por ler o identificador do comando a executar e defere o controlo para o candidato, ou retorna ou erro, caso nenhum candidato aceite o identificador. O candidato analisa então o código-fonte caráter a caráter, separando os argumentos nos suas tokens individuais e validando a sua sintáxe. Caso os argumentos sejam sintáticamente válidos, o candidato analisa então cada argumento e valida se o seu valor na sua posição é correto para o comando em questão. Caso os tokens sejam válidos, é construída uma instância do comando populada com os mesmos.

#### Execução
A segunda fase analisa os tokens que constituem os argumentos e verifica a validade semântica dos mesmos em relação ao estado global da máquina, convertendo-os para os seus valores úteis em caso positivo, ou parando a sua execução e retornando um erro em caso negativo. Após a transformação bem-sucedida dos argumentos, o comando é executado, modificando o estado da máquina e retornando uma mensagem para ser exibida ao utilizador.

### Extras
Além dos comandos exibidos no exemplo (**LISTAR**, **MOEDA**, **SELECIONAR**, **...**, **SAIR**), implementei também os seguintes comandos:
- **EJETAR**: Ejeta o crédito atualmente inserido na máquina sob a forma de moedas. O sistema tenta retornar o valor em moedas de maior valor antes de usar as moedas de menor valor.
- **LIMPAR**: Limpa a interface de utilizador.
- **AJUDA**: Lista os comandos disponíveis juntamente com a sua descrição, ou a informação acerca de um comando. Comandos de manuntenção são escondidos do utilizador se não tiver uma sessão iniciada.
- **MANUNTENÇÃO**: Inicia uma sessão de manuntenção ao fornecer uma palavra-passe, ou termina uma sessão quando chamado sem argumentos.
- **ADICIONAR**: Adiciona mais unidades de um dado produto ao stock.
- **MODIFICAR**: Um multi-comando que permite a manipulação de produtos individuais no stock.
  - **ADD**: Adiciona um novo produto ao stock, caracterizado pelos seus atributos `código`, `nome`, `quant` e `preco`.
  - **EDIT**: Modifica uma propriedade de um produto existente no stock.
    - **preco**: Modifica o preço de um produto.
  - **REMOVE**: Remove uma ou mais unidades (`quant`) de um produto existente no stock, identificado pelo seu `código`. Caso `quant` seja `all`, todas as unidades desse produto são removidas.

Os comandos **MANUNTENÇÃO**, **ADICIONAR** e **MODIFICAR** são escondidos do utilizador se ele não poissuír uma sessão de manuntenção ativa.

Além dos comandos extra, foi implementado um sistema de histórico de comandos da sessão de execução atual da máquina, acessível através das setas para cima e para baixo, por conveniência.

### Resultados
O programa pode ser executado através do comando:
```
$ python3 maquina.py
```
