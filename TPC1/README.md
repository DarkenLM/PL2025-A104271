# TPC 1

**Titulo:** Somador on/off  
**Autor:** Rafael Santos Fernandes  

## Resumo
### Enunciado
1. Pretende-se um programa que some todas as sequências de dígitos que encontre num texto;
2. Sempre que encontrar a string "Off" em qualquer combinação de maiúsculas e minúsculas, esse comportamento é desligado;
3. Sempre que encontrar a string "On" em qualquer combinação de maiúsculas e minúsculas, esse comportamento é novamente ligado;
4. Sempre que encontrar o caráter "=", o resultado da soma é colocado na saída.

### Resolução
Com a informação presente no enunciado, o comportamento da operação to caractere "=" é ambíguo nas situações em que o programa se encontra num estado de controlo "Off". Nesta resolução, foi assumido que tal operação ocorre tanto em estados "On" como em estados "Off".

Para determinar os tokens de controlo ("Off" e "On", em qualquer capitalização), são efetuados dois lookaheads, de um e dois caracteres, e compara-se o seu valor em minúsculas com "on" e "off", respetivamente. Caso uma dessas comparações resulte num valor verdadeiro, o estado de controlo do programa é mudado para o correspondente estado do token.

As sequências de digitos são determinadas ao acumular todos os digitos contíguos a um digito inicialmente detetado. As sequências são então convertidas para um inteiro e somadas a um acumulador global. Esta operação não ocorrem quando o programa se encontra num estado de controlo "Off".


### Resultados
> A resolução deste TPC inclui uma suíte de testes automáticos que permite testar automaticamente o programa.  
Para correr a suíte de testes, execute o script `test.sh`. Os resultados da suíte de testes serão apresentados num ficheiro `results.md`, contendo um resumo dos testes executados. Adicionalmente, será também criado um diretório `logs`, que contém um ficheiro de logs indivídual para cada teste.

Um ficheiro resultante da última execução da suíte de testes encontra-se disponível: [Resultados](./results_2025-02-08T02:29:39.md).
