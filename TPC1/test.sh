#!/bin/zsh

#####################################################################################
# test.sh
# Basic test runner for python scripts, with result summary and independent logging.
# Supported test cases are simple equality matches.
# 
# Version: 1.2.0
# Author: DarkenLM
#####################################################################################

# Color codes
GREEN="\033[1;32m"
RED="\033[1;31m"
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RESET="\033[0m"

# Icons
PASS_ICON="✅"
FAIL_ICON="❌"

# Python script location
TARGET_EXE="sum_ints.py"
SUITE_RESULTS_FILE="results.md"

# This function defines the structure of the log file for each test.
#
#   @param {string} LOG_FILE is the log file for the current test.
#   @param {string} NAME is the name of the current test, usually "test/<name>.txt".
#   @param {string} TIMESTAMP is the datetime the test was started, in a ISO-8601-like structure.
#   @param {string} STATUS is a string representing the final status for the given test.
#   @param {string} INPUT is the input used for the test.
#   @param {string} OUTPUT is the output collected from the test run.
#   @param {string?} EXPECTED is the expected output for the test. Undefined if the test passed.
WRITE_TO_LOG() {
  LOG_FILE=$1
  NAME=$2
  TIMESTAMP=$3
  STATUS=$4
  INPUT=$5
  OUTPUT=$6
  EXPECTED=$7

  {
    echo "# Test: $NAME"
    echo "# Ran at: $TIMESTAMP"
    echo "# Status: $STATUS"
    echo ""
    echo "# ============== INPUT =============="
    echo "$INPUT"
    echo ""
    if [[ ! -z "$EXPECTED" ]] then  
      echo "# ============== EXPECTED =============="
      echo "$EXPECTED"
      echo ""
    fi
    echo "# ============== OUTPUT =============="
    echo "$OUTPUT"
  } > "$LOG_FILE"
}

# This function defines the structure of the test suite results file header.
# This function makes use of a substitution token (SUITE_SUMMARY) that is later processed by WRITE_SUITE_RESULTS.
#
#   @param {string} LOG_FILE is the results file.
#   @param {string} TIMESTAMP is the datetime the test was started, in a ISO-8601-like structure.
WRITE_SUITE_HEADER() {
  LOG_FILE=$1
  TIMESTAMP=$2

  {
    echo "# Test suite results"
    echo "Ran at: $TIMESTAMP"
    echo ""
    echo "SUITE_SUMMARY"
    # echo "# ============== RESULTS =============="
    echo "## Results"
  } > "$LOG_FILE"
}

# This function defines the way each test result is written to the test suite results file.
# By default, it is merely a proxy that adds a markdown newline to each.
# 
#   @param {string} LOG_FILE is the results file.
#   @param {string} RESULT is the already formatted result.
WRTIE_SUITE_RESULT() {
  LOG_FILE=$1
  RESULT=$2

  {
    echo "$RESULT  "
  } >> "$LOG_FILE"
}

# This function defines the structure of the test suite results file summary.
# This function processes the substitution token SUITE_SUMMARY defined by WRITE_SUITE_HEADER and populates
# it with the summary for the test suite.
#
#   @param {string} LOG_FILE is the results file.
#   @param {number} PASSED is the number of tests that successfully passed.
#   @param {number} FAILED is the number of tests that have failed.
#   @param {number} TOTAL is the total number of tests that have been executed.
WRITE_SUITE_RESULTS() {
  LOG_FILE=$1
  PASSED=$2
  FAILED=$3
  TOTAL=$4

  _SUMMARY=""
  _SUMMARY+="## Test Summary:\n"
  _SUMMARY+="**🧮 Total:**  $TOTAL  \n"
  _SUMMARY+="**$PASS_ICON Passed:** $PASSED / $TOTAL  \n"
  _SUMMARY+="**$FAIL_ICON Failed:** $FAILED / $TOTAL  \n"
  # sed -i "s/SUITE_SUMMARY/$_SUMMARY/g" "$LOG_FILE"
  awk "{
    gsub(/SUITE_SUMMARY/, \"$_SUMMARY\"); print
  }" "$LOG_FILE" > "${LOG_FILE}_tmp" && mv "${LOG_FILE}_tmp" "$LOG_FILE"
}

# Check if target executable exists
if [[ ! -f "$TARGET_EXE" ]]; then
  echo -e "${RED}Error: Target executable '$TARGET_EXE' not found.${RESET}"
  exit 1
fi

# Create logs directory if it does not exist
mkdir -p logs

TOTAL=0
PASSED=0
FAILED=0

echo -e "${CYAN}Running tests...${RESET}"
echo "----------------------"

SUITE_TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
WRITE_SUITE_HEADER $SUITE_RESULTS_FILE $SUITE_TIMESTAMP

for test_file in tests/*.txt; do
  TOTAL=$((TOTAL + 1))
  
  # Read input and expected output from each test
  TEST_INPUT=$(head -n 1 "$test_file")
  EXPECTED_OUTPUT=$(tail -n +2 "$test_file")

  # Prepare logging for the test
  TEST_NAME=$(basename "$test_file" .txt)
  LOG_FILE="logs/${TEST_NAME}.log"
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  # Run the target executable and capture output
  ACTUAL_OUTPUT=$(echo "$TEST_INPUT" | python3 "$TARGET_EXE" 2>&1)

  if [[ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]]; then
    WRITE_TO_LOG $LOG_FILE $TEST_NAME $TIMESTAMP "$PASS_ICON PASS" $TEST_INPUT $ACTUAL_OUTPUT
    echo -e "$PASS_ICON ${GREEN}PASS:${RESET} $test_file"
    WRTIE_SUITE_RESULT $SUITE_RESULTS_FILE "$PASS_ICON **PASS:** $test_file"
    PASSED=$((PASSED + 1))
  else
    ACTUAL_OUTPUT_TRIMMED=$(echo "$ACTUAL_OUTPUT" | tail -n 5)

    WRITE_TO_LOG $LOG_FILE $TEST_NAME $TIMESTAMP "$FAIL_ICON FAIL" $TEST_INPUT $ACTUAL_OUTPUT $EXPECTED_OUTPUT

    # Write to stdout
    echo -e "$FAIL_ICON ${RED}FAIL:${RESET} $test_file"
    echo -e "   📥 Input:    '$TEST_INPUT'"
    echo -e "   🔹 Expected: '${EXPECTED_OUTPUT}'"
    echo -e "   🔸 Got (last 5 lines):"
    echo -e "${YELLOW}${ACTUAL_OUTPUT_TRIMMED}${RESET}"
    echo -e "   📝 Log saved: ${YELLOW}$LOG_FILE${RESET}"

    # Write to results file. Kinda repeated code because I'm not feeling like stripping the ANSI codes in bash.
    _FAIL_RESULT=""
    _FAIL_RESULT+="**$FAIL_ICON FAIL:** $test_file  \n"
    _FAIL_RESULT+="   - 📥 Input:    '$TEST_INPUT'  \n"
    _FAIL_RESULT+="   - 🔹 Expected: '${EXPECTED_OUTPUT}'  \n"
    _FAIL_RESULT+="   - 🔸 Got (last 5 lines):  \n"
    _FAIL_RESULT+="\`\`\`\n${ACTUAL_OUTPUT_TRIMMED}\n\`\`\`  \n"
    _FAIL_RESULT+="   - 📝 Log saved: $LOG_FILE  \n"

    WRTIE_SUITE_RESULT $SUITE_RESULTS_FILE $_FAIL_RESULT

    FAILED=$((FAILED + 1))
  fi
done

# Final summary
echo "----------------------"
echo -e "${CYAN}Test Summary:${RESET}"
echo -e "$PASS_ICON Passed: ${GREEN}$PASSED${RESET} / $TOTAL"
echo -e "$FAIL_ICON Failed: ${RED}$FAILED${RESET} / $TOTAL"

WRITE_SUITE_RESULTS $SUITE_RESULTS_FILE $PASSED $FAILED $TOTAL

# Exit code based on success/failure
if [[ $FAILED -gt 0 ]]; then
  exit 1
else
  exit 0
fi
