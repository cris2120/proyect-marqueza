class PasswordRecoveryForm {
    constructor(form) {
        this.form = form;
        this.email = form.querySelector('#correo');
    }

    async submit(event) {
        event.preventDefault();
        const correo = this.email.value.trim();
        if (!this.email.checkValidity()) {
            Swal.fire({ icon: 'warning', title: 'Correo inválido', text: 'Ingresa un correo electrónico válido.' });
            return;
        }

        const button = this.form.querySelector('button');
        button.disabled = true;
        button.classList.add('is-loading');
        try {
            await window.MarquezaApi.requestPasswordReset(correo);
            await Swal.fire({ icon: 'success', title: 'Solicitud recibida', text: 'Si existe una cuenta con ese correo, el administrador revisará la solicitud.', confirmButtonText: 'Entendido' });
            this.form.reset();
        } catch (error) {
            await window.MarquezaApi.notifyError(error, 'No se pudo registrar la solicitud');
        } finally {
            button.disabled = false;
            button.classList.remove('is-loading');
        }
    }

}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recoveryForm');
    if (form) form.addEventListener('submit', event => new PasswordRecoveryForm(form).submit(event));
});
