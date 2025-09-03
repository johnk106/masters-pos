function myFunction(event) {
  let inputField = document.querySelector(".input");

  if (/[0-9+\-*/%.]/.test(event.key)) {
    dis(event.key);
  } else if (event.key === "Backspace" || event.key === "Delete") {
    back();
  } else if (event.key === "Enter" || event.key === "=") {
    solve();
  } else if (event.key === "c" || event.key === "C") {
    clr();
  }
}

// Add keyboard support when calculator modal is open
document.addEventListener('DOMContentLoaded', function() {
  const calculatorModal = document.getElementById('calculator');
  
  if (calculatorModal) {
    calculatorModal.addEventListener('shown.bs.modal', function() {
      document.addEventListener('keydown', myFunction);
      document.getElementById('calculator-input').focus();
    });
    
    calculatorModal.addEventListener('hidden.bs.modal', function() {
      document.removeEventListener('keydown', myFunction);
    });
  }
});

function solve() {
  let inputField = document.querySelector(".input");
  let expression = inputField.value;

  // Handle empty input
  if (!expression || expression.trim() === "") {
    inputField.value = "0";
    return;
  }

  try {
    // Replace division by zero check
    if (expression.includes("/0") && !expression.includes("/00")) {
      inputField.value = "Error: Division by zero";
      return;
    }
    
    // Clean the expression and evaluate
    let cleanExpression = expression.replace(/×/g, '*').replace(/÷/g, '/');
    let result = eval(cleanExpression);
    
    // Handle special cases
    if (result === Infinity || result === -Infinity) {
      inputField.value = "Error: Division by zero";
    } else if (isNaN(result)) {
      inputField.value = "Error: Invalid operation";
    } else {
      // Round to avoid floating point precision issues
      inputField.value = Math.round(result * 1000000000) / 1000000000;
    }
  } catch (error) {
    inputField.value = "Error: Invalid expression";
  }
}

function clr() {
  document.querySelector(".input").value = "";
}

function back() {
  let inputField = document.querySelector(".input");
  inputField.value = inputField.value.slice(0, -1);
}

function dis(val) {
  let inputField = document.querySelector(".input");
  let currentValue = inputField.value;
  
  // Clear error messages before new input
  if (currentValue.includes("Error")) {
    inputField.value = "";
    currentValue = "";
  }
  
  // Prevent multiple consecutive operators
  if (['+', '-', '*', '/'].includes(val) && ['+', '-', '*', '/'].includes(currentValue.slice(-1))) {
    return;
  }
  
  // Prevent multiple decimal points in the same number
  if (val === '.') {
    let lastOperatorIndex = Math.max(
      currentValue.lastIndexOf('+'),
      currentValue.lastIndexOf('-'),
      currentValue.lastIndexOf('*'),
      currentValue.lastIndexOf('/'),
      currentValue.lastIndexOf('×'),
      currentValue.lastIndexOf('÷')
    );
    let currentNumber = currentValue.substring(lastOperatorIndex + 1);
    if (currentNumber.includes('.')) {
      return;
    }
  }
  
  inputField.value += val;
}