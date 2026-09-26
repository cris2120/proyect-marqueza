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
            await window.MarquezaApi.post('/auth/forgot-password', { correo });
            await Swal.fire({ icon: 'success', title: 'Solicitud enviada', text: 'Si la cuenta existe, recibirás instrucciones para restablecer la contraseña.', confirmButtonText: 'Entendido' });
            this.form.reset();
        } catch (error) {
            Swal.fire({ icon: 'error', title: 'No se pudo solicitar la recuperación', text: error.message });
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
