function transfer(address) {
    fetch(`http://127.0.0.1:8000/transfer/${address}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.log(`Error: ${data.error}`);
        } else {
            const responseDiv = document.getElementById('faucet-response');
            const transactionData = data.transaction_data.split(' ');
            let transactionOutput = '';
            transactionData.forEach((item) => {
                const keyValue = item.split('=');
                const key = keyValue[0];
                const value = keyValue[1];
                transactionOutput += `"${key}": ${value}<br>`;
            });
            responseDiv.innerHTML = `<pre>${transactionOutput}</pre>`;
        }
      })
      .catch(error => {
        console.log(`Error: ${error.message}`);
      });
}

function callFaucet() {
    const addressInput = document.getElementById('faucet-request');
    const address = addressInput.value;

    transfer(address);
}