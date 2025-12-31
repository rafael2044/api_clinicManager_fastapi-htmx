(function () {
        if (typeof IMask !== "undefined") {
            const inputCpf = document.getElementById("input-cpf");
            const inputContact = document.getElementById("input-contact");
            const maskCpf = {
                mask: "000.000.000-00",
            };
            const maskContact = {
                mask: "(00) 0 0000-0000",
            };
            IMask(inputCpf, maskCpf);
            IMask(inputContact, maskContact);
        }
    })();