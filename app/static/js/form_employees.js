(function () {
        if (typeof IMask !== "undefined") {
            const inputCpf = document.getElementById("input-cpf");
            const maskCpf = {
                mask: "000.000.000-00",
            };
            IMask(inputCpf, maskCpf);
        }
    })();
    // Script simples para simular o comportamento de abas (estilo do botão)
    document.body.addEventListener('htmx:afterOnLoad', function(evt) {
        if (evt.detail.target.id === 'dynamic-form-section') {
            const isDoc = evt.detail.xhr.responseURL.includes('role=doctor');
            const btnDoc = document.getElementById('btn-doctor');
            const btnAdm = document.getElementById('btn-admin');
            const submitBtn = document.getElementById('submit-btn');

            if (isDoc) {
                btnDoc.classList.add('bg-white', 'text-blue-600', 'shadow-sm');
                btnDoc.classList.remove('text-gray-500');
                btnAdm.classList.add('text-gray-500');
                btnAdm.classList.remove('bg-white', 'text-purple-600', 'shadow-sm');
                submitBtn.classList.replace('bg-purple-600', 'bg-blue-600');
            } else {
                btnAdm.classList.add('bg-white', 'text-purple-600', 'shadow-sm');
                btnAdm.classList.remove('text-gray-500');
                btnDoc.classList.add('text-gray-500');
                btnDoc.classList.remove('bg-white', 'text-blue-600', 'shadow-sm');
                submitBtn.classList.replace('bg-blue-600', 'bg-purple-600');
            }
        }
    });