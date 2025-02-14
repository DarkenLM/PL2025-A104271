# TPC 2

**Titulo:** Análise de um dataset de obras musicais  
**Data:**  2025-02-11  
**Autor:** Rafael Santos Fernandes  
**Número:** A104271  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
### Enunciado
1. Neste TPC, é proibido usar o módulo CSV do Python;
2. Deverás ler o dataset, processá-lo e criar os seguintes resultados:
    - Lista ordenada alfabeticamente dos compositores musicais;
    - Distribuição das obras por período: quantas obras catalogadas em cada período;
    - Dicionário em que a cada período está a associada uma lista alfabética dos títulos das obras desse período.

### Resolução
Para a resolução deste TPC, comecei por examinar os dados contidos no dataset fornecido e retirei as seguintes conclusões:
- O dataset é uma tabela com 7 colunas.
- Os dados da segunda coluna, "desc", são strings delimitadas por quotes (`"`), que podem conter outras quotes dentro, escapadas com `""`. As strings podem ocupar múltiplas linhas de texto, identadas com whitespace em cada linha adicional.
- Os dados da quinta coluna, "compositor" não se encontram num formato consistente: algumas das linhas separam o último nome do compositor e colocam-no no início, separado do resto do nome com uma vírgula (ex.: `Krebs, Johann Ludwig`), enquanto outras linhas contém o nome completo na sua ordem natural (ex.: `Marc-Antoine Charpentier`).

Decidi então tomar as seguintes decisões de modo a interpretar corretamente os dados no seu carregamento para o sistema:
- A leitura de um caractere `"` altera o modo de leitura para `capture`, substituindo a interpretação normal dos caracteres até encontrar outro caractere do mesmo tipo. Durante este modo: 
    - As sequências de caracteres `""` são interpretadas e adicionadas ao acumulador atual como `"`.
    - O espaço em branco imediatamente depois do caractere `\n` é removido, tal como o próprio caractere.
    - O caractere `"` altera o modo de leitura para `normal`, se e só se não existir um segundo caractere do mesmo tipo imediatamente a seguir.

Decidi também pós-processar os dados carregados para o sistema, de modo a os normalizar, facilitando o seu uso posterior. O pós-processamento consiste únicamente na normalização dos nomes dos compositores para a sua ordem natural, já que as decisões tomadas para o sistema de leitura corrige os restantes problemas. 

### Resultados
O programa cria três ficheiros, [`result_composers.json`](./result_composers.json), [`result_periods.json`](./result_periods.json) e [`result_mixed.json`](./result_mixed.json), que contém estruturas em JSON contendo os dados pedidos em cada alínea do enunciado:
- `result_composers.json`: "Lista ordenada alfabeticamente dos compositores musicais;"
- `result_periods.json`: "Distribuição das obras por período: quantas obras catalogadas em cada período;"
- `result_mixed.json`: "Dicionário em que a cada período está a associada uma lista alfabética dos títulos das obras desse período.
