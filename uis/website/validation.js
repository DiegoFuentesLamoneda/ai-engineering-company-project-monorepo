/**
 * Validación del formulario de registro de talento de Nexova.
 *
 * Los mensajes de error son literalmente los que fija el contexto del hito
 * (CONTEXT.md → "Mensajes de error esperados"). No se reformulan.
 *
 * El formulario lleva `novalidate` para que el navegador no muestre sus
 * propios bocadillos, pero los inputs conservan `required`, `min` y `max`:
 * así el HTML sigue describiendo sus restricciones para los lectores de
 * pantalla aunque la comprobación la haga este archivo.
 */
(function () {
  'use strict';

  var formulario = document.getElementById('formulario-talento');
  if (!formulario) return;

  var LIMITE_COMENTARIOS = 500;

  // Clases escritas enteras a propósito: Tailwind escanea este archivo y solo
  // genera las que encuentra como texto literal.
  var BORDE_ERROR = 'border-red-500';
  var BORDE_EXITO = 'border-emerald-500';

  // Los controles usan border-slate-300 y los contenedores border-slate-200.
  // Hay que quitar ambas al pintar un estado: si se deja la neutra puesta,
  // compite con la de color a igual especificidad y gana la que Tailwind haya
  // emitido más abajo en la hoja, que no controlamos.
  var BORDES_NEUTROS = ['border-slate-200', 'border-slate-300'];

  /** Teléfono en formato internacional: entre 8 y 15 dígitos tras el "+". */
  function telefonoValido(valor) {
    return /^\+\d{8,15}$/.test(valor.replace(/[\s-]/g, ''));
  }

  function emailValido(valor) {
    return /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(valor);
  }

  function urlValida(valor) {
    if (!/^https?:\/\//i.test(valor)) return false;
    try {
      return Boolean(new URL(valor).hostname);
    } catch (error) {
      return false;
    }
  }

  /**
   * Reglas por campo. Cada una devuelve el mensaje de error, o null si es
   * válido. El orden marca a qué campo se lleva el foco al fallar el envío.
   */
  var CAMPOS = [
    {
      nombre: 'nombre_completo',
      valida: function (valor) {
        var palabras = valor.trim().split(/\s+/).filter(Boolean);
        return palabras.length >= 2
          ? null
          : 'El nombre debe contener al menos nombre y apellido';
      }
    },
    {
      nombre: 'email',
      valida: function (valor) {
        return emailValido(valor.trim())
          ? null
          : 'Ingresa un email válido (ejemplo: nombre@empresa.com)';
      }
    },
    {
      nombre: 'telefono',
      valida: function (valor) {
        return telefonoValido(valor.trim())
          ? null
          : 'El teléfono debe incluir código de país (ejemplo: +34 612 345 678)';
      }
    },
    {
      nombre: 'pais_residencia',
      valida: function (valor) {
        return valor ? null : 'Selecciona tu país de residencia';
      }
    },
    {
      nombre: 'anios_experiencia',
      valida: function (valor) {
        var texto = valor.trim();
        var numero = Number(texto);
        var correcto = texto !== '' && Number.isInteger(numero)
          && numero >= 0 && numero <= 50;
        return correcto
          ? null
          : 'Los años de experiencia deben estar entre 0 y 50';
      }
    },
    {
      nombre: 'sector_interes',
      valida: function (valor) {
        return valor ? null : 'Selecciona el sector de tu interés';
      }
    },
    {
      nombre: 'nivel_ingles',
      valida: function (valor) {
        return valor ? null : 'Indica tu nivel de inglés';
      }
    },
    {
      nombre: 'disponibilidad',
      grupoRadio: true,
      valida: function (valor) {
        return valor ? null : 'Selecciona tu disponibilidad';
      }
    },
    {
      nombre: 'linkedin_url',
      opcional: true,
      valida: function (valor) {
        var texto = valor.trim();
        if (texto === '') return null;
        return urlValida(texto)
          ? null
          : 'Si incluyes LinkedIn, debe ser una URL válida';
      }
    },
    {
      nombre: 'comentarios',
      opcional: true,
      valida: function (valor) {
        if (valor.length <= LIMITE_COMENTARIOS) return null;
        // La plantilla del enunciado lleva "(quedan X)". Cuando se supera el
        // límite no queda ninguno, así que X es 0; el contador en vivo es el
        // que indica cuántos caracteres sobran.
        var quedan = Math.max(0, LIMITE_COMENTARIOS - valor.length);
        return 'Los comentarios no pueden exceder ' + LIMITE_COMENTARIOS +
          ' caracteres (quedan ' + quedan + ')';
      }
    },
    {
      nombre: 'politica_datos',
      casilla: true,
      valida: function (marcada) {
        return marcada
          ? null
          : 'Debes aceptar la política de tratamiento de datos para continuar';
      }
    }
  ];

  /** Devuelve el control (o el primero del grupo) de un campo. */
  function control(campo) {
    if (campo.grupoRadio) {
      return formulario.querySelector('[name="' + campo.nombre + '"]');
    }
    return document.getElementById(campo.nombre);
  }

  /** Valor actual del campo, normalizado según su tipo. */
  function valor(campo) {
    if (campo.casilla) return document.getElementById(campo.nombre).checked;
    if (campo.grupoRadio) {
      var marcado = formulario.querySelector('[name="' + campo.nombre + '"]:checked');
      return marcado ? marcado.value : '';
    }
    return document.getElementById(campo.nombre).value;
  }

  /** Contenedor al que se le pinta el borde rojo en radios y casillas. */
  function contenedor(campo) {
    var elemento = control(campo);
    if (!elemento) return null;
    if (campo.grupoRadio) return elemento.closest('fieldset');
    if (campo.casilla) return elemento.closest('div');
    return elemento;
  }

  function pintaEstado(campo, hayError, hayValor) {
    var caja = contenedor(campo);
    if (!caja) return;

    // Recordamos con qué borde neutro nació el elemento para poder devolverlo.
    if (!caja.dataset.bordeOriginal) {
      caja.dataset.bordeOriginal = BORDES_NEUTROS.filter(function (clase) {
        return caja.classList.contains(clase);
      })[0] || 'border-slate-300';
    }

    caja.classList.remove(BORDES_NEUTROS[0], BORDES_NEUTROS[1], BORDE_ERROR, BORDE_EXITO);
    if (hayError) {
      caja.classList.add(BORDE_ERROR);
    } else if (hayValor) {
      caja.classList.add(BORDE_EXITO);
    } else {
      caja.classList.add(caja.dataset.bordeOriginal);
    }
  }

  /** Valida un campo y actualiza mensaje, aria-invalid y estado visual. */
  function revisa(campo) {
    var elemento = control(campo);
    if (!elemento) return true;

    var actual = valor(campo);
    var mensaje = campo.valida(actual);
    var aviso = document.getElementById('error-' + campo.nombre);
    var lleno = campo.casilla ? actual : String(actual).trim() !== '';

    if (aviso) {
      aviso.textContent = mensaje || '';
      aviso.hidden = !mensaje;
    }

    var controles = campo.grupoRadio
      ? formulario.querySelectorAll('[name="' + campo.nombre + '"]')
      : [elemento];
    Array.prototype.forEach.call(controles, function (uno) {
      if (mensaje) {
        uno.setAttribute('aria-invalid', 'true');
      } else {
        uno.removeAttribute('aria-invalid');
      }
    });

    pintaEstado(campo, Boolean(mensaje), lleno);
    return !mensaje;
  }

  function limpiaCampo(campo) {
    var aviso = document.getElementById('error-' + campo.nombre);
    if (aviso) {
      aviso.textContent = '';
      aviso.hidden = true;
    }
    var controles = campo.grupoRadio
      ? formulario.querySelectorAll('[name="' + campo.nombre + '"]')
      : [control(campo)];
    Array.prototype.forEach.call(controles, function (uno) {
      if (uno) uno.removeAttribute('aria-invalid');
    });
    pintaEstado(campo, false, false);
  }

  // ---------------------------------------------------------------------
  // Contador de comentarios
  // ---------------------------------------------------------------------
  var comentarios = document.getElementById('comentarios');
  var contador = document.getElementById('contador-comentarios');

  function actualizaContador() {
    if (!comentarios || !contador) return;
    var usados = comentarios.value.length;
    contador.textContent = usados + ' / ' + LIMITE_COMENTARIOS;
    contador.classList.toggle('text-red-700', usados > LIMITE_COMENTARIOS);
    contador.classList.toggle('text-slate-500', usados <= LIMITE_COMENTARIOS);
  }

  // ---------------------------------------------------------------------
  // Validación en vivo
  // ---------------------------------------------------------------------
  CAMPOS.forEach(function (campo) {
    var controles = campo.grupoRadio
      ? formulario.querySelectorAll('[name="' + campo.nombre + '"]')
      : [control(campo)];

    Array.prototype.forEach.call(controles, function (elemento) {
      if (!elemento) return;

      // Al salir del campo se valida siempre.
      elemento.addEventListener('blur', function () { revisa(campo); });

      // Mientras se escribe solo se revalida si ya estaba marcado como
      // erróneo, para no señalar en rojo un campo a medio escribir.
      elemento.addEventListener('input', function () {
        if (elemento.getAttribute('aria-invalid') === 'true') revisa(campo);
      });

      // Selects, radios y casillas se resuelven de una vez.
      if (campo.grupoRadio || campo.casilla || elemento.tagName === 'SELECT') {
        elemento.addEventListener('change', function () { revisa(campo); });
      }
    });
  });

  if (comentarios) {
    comentarios.addEventListener('input', actualizaContador);
    actualizaContador();
  }

  // ---------------------------------------------------------------------
  // Envío
  // ---------------------------------------------------------------------
  var resumen = document.getElementById('resumen-errores');
  var resumenTexto = document.getElementById('resumen-errores-texto');
  var exito = document.getElementById('mensaje-exito');

  formulario.addEventListener('submit', function (evento) {
    evento.preventDefault();

    var invalidos = CAMPOS.filter(function (campo) { return !revisa(campo); });

    if (invalidos.length > 0) {
      if (resumen && resumenTexto) {
        resumenTexto.textContent = invalidos.length === 1
          ? 'Hay 1 campo que necesita tu atención. Revísalo antes de enviar.'
          : 'Hay ' + invalidos.length + ' campos que necesitan tu atención. Revísalos antes de enviar.';
        resumen.hidden = false;
      }
      var primero = control(invalidos[0]);
      if (primero) primero.focus();
      return;
    }

    if (resumen) resumen.hidden = true;

    // Envío simulado: el hito no pide conectar el formulario a ningún sitio.
    formulario.hidden = true;
    if (exito) {
      exito.hidden = false;
      exito.setAttribute('tabindex', '-1');
      exito.focus();
      exito.scrollIntoView({ block: 'start' });
    }
  });

  // ---------------------------------------------------------------------
  // Limpiar
  // ---------------------------------------------------------------------
  // El reset nativo vacía los valores, pero deja los mensajes de error, los
  // aria-invalid y los bordes de colores tal cual estaban.
  formulario.addEventListener('reset', function () {
    window.setTimeout(function () {
      CAMPOS.forEach(limpiaCampo);
      if (resumen) resumen.hidden = true;
      actualizaContador();
      var primero = document.getElementById('nombre_completo');
      if (primero) primero.focus();
    }, 0);
  });
})();
