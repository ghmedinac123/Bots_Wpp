const { createBot, createProvider, createFlow,  addKeyword,EVENTS } = require('@bot-whatsapp/bot');
const MongoAdapter = require('@bot-whatsapp/database/mongo');
const QRPortalWeb = require('@bot-whatsapp/portal');
const BaileysProvider = require('@bot-whatsapp/provider/baileys');
const MySQLAdapter = require('@bot-whatsapp/database/mysql');
const axios = require('axios');
const path = require("path");
const fs = require("fs");
const { exec } = require('child_process');

const{ handlerAI }=require("./whisper.js")

const menuPath = path.join(__dirname, "mensajes", "menu.txt");
const menu = fs.readFileSync(menuPath, "utf-8"); 

const menuPath2 = path.join(__dirname, "mensajes", "menu_planes.txt");
const menu_planes = fs.readFileSync(menuPath2, "utf-8");

const menuPath3 = path.join(__dirname, "mensajes", "sector_urbano.txt");
const plan_urbano = fs.readFileSync(menuPath3, "utf-8");


const menuPath4 = path.join(__dirname, "mensajes", "sector_rural.txt");
const plan_rural = fs.readFileSync(menuPath4, "utf-8");

const menuPath5 = path.join(__dirname, "mensajes", "sector_rural_sanroque.txt");
const plan_rural_sanroque = fs.readFileSync(menuPath5, "utf-8");

const menuPath6 = path.join(__dirname, "mensajes", "sector_rural_quituro.txt");
const plan_rural_quituro = fs.readFileSync(menuPath6, "utf-8");

const menuPath7 = path.join(__dirname, "mensajes", "sector_rural_sanadolfo.txt");
const plan_rural_sanadolfo = fs.readFileSync(menuPath7, "utf-8");

const menuPath8 = path.join(__dirname, "mensajes", "sector_rural_caserio.txt");
const plan_rural_caserio = fs.readFileSync(menuPath8, "utf-8");


const BOTNAME = 'bot'
QRPortalWeb({ name: BOTNAME, port: 3052 })

/**
 * Declaramos las conexiones de MySQL
 */
const MYSQL_DB_HOST = 'localhost'
const MYSQL_DB_USER = 'root'
const MYSQL_DB_PASSWORD = 'GBBGH4R53A8FGLS'
const MYSQL_DB_NAME = 'bots'
const MYSQL_DB_PORT = '3306'
/**
 * Declaramos las conexiones MONGODB
 */
const adapterDB = new MongoAdapter({
    dbUri: 'mongodb://198.50.181.104:27017',
    dbName: 'db_bot',
 })

//Función para predecir cobertura a partir de coordenadas usando tu API
const predictCoverageFromCoordinates = async (latitude, longitude) => {
    try {
        console.log(`🔄 Enviando coordenadas a la API de predicción: Latitud ${latitude}, Longitud ${longitude}`);
        const response = await axios.post('http://198.50.181.104:8001/predict', {
            coordinates: `${latitude},${longitude}`
        }, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = response.data;
        console.log(`🔄 Respuesta de la API: ${JSON.stringify(data)}`);
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Manejo de la respuesta de cobertura
        const hasCoverage = data.coverage === 'Sí' || data.coverage === 'S\u00ed';
        return {
            hasCoverage: hasCoverage,
            coordinates: data.coordinates
        };
    } catch (error) {
        console.error(`❌ Error de la API: ${error}`);
        throw error;
    }
}
// Función para consultar el chatbot externo
const queryExternalChatbot = async (message) => {
    try {
        const response = await axios.post('http://198.50.181.104:5000/chat', {
            message: message
        }, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        console.log('🤖 Chatbot API conectado correctamente.');
        return response.data.reply;
    } catch (error) {
        console.error('❌ Error conectando a la Chatbot API:', error);
        return null;
    }
};
// Función para extraer y limpiar la dirección del mensaje
function extractAddress(messageText) {
    const regex = new RegExp(`\\b(${addressKeywords.join('|')})\\b.*`, 'i');
    const match = messageText.match(regex);
    return match ? match[0] : null;
}

async function transcribeAudio(audioPath) {
    return new Promise((resolve, reject) => {
        exec(`python /home/FututelBots/newBots2/base-baileys-mysql/transcribe_api_key.py ${audioPath}`, (error, stdout, stderr) => {
            if (error) {
                reject(`Error al ejecutar el script de Python: ${error.message}`);
                return;
            }
            if (stderr) {
                reject(`Error en el script de Python: ${stderr}`);
                return;
            }

            console.log("Respuesta del script de Python:", stdout);

            try {
                const responseData = JSON.parse(stdout);
                if (responseData.transcript) {
                    resolve(responseData.transcript);
                } else {
                    reject(responseData.error || "Error desconocido al procesar la transcripción.");
                }
            } catch (e) {
                reject(`Error al parsear la respuesta del script de Python: ${e.message}`);
            }
        });
    });
}

const flowVoice = addKeyword(EVENTS.VOICE_NOTE).addAnswer("Esta es una nota de voz Voy a Procesarla con IA", null, async (ctx, ctxFn) => {
    try {
        const audioUrl = ctx.message.audioMessage.url;
        const audioPath = '/home/FututelBots/newBots2/base-baileys-mysql/input.ogg';

        // Descargar el archivo de audio
        const audioResponse = await axios.get(audioUrl, { responseType: 'arraybuffer' });
        fs.writeFileSync(audioPath, audioResponse.data);

        const text = await transcribeAudio(audioPath);

        if (!text || text === "ERROR") {
            console.log("Error en la conversión de voz a texto.");
            if (typeof ctxFn.flowDynamic === 'function') {
                await ctxFn.flowDynamic([{ body: "Lo siento, hubo un error al procesar la nota de voz." }]);
            } else {
                console.error("ctxFn.flowDynamic no es una función. Métodos disponibles en ctxFn:", Object.keys(ctxFn));
            }
        } else {
            console.log("Texto transcrito:", text);

            // Consultar el chatbot externo con la transcripción
            const chatbotResponse = await queryExternalChatbot(text);

            if (!chatbotResponse) {
                if (typeof ctxFn.flowDynamic === 'function') {
                    await ctxFn.flowDynamic([{ body: "Lo siento, hubo un error al obtener una respuesta del chatbot." }]);
                } else {
                    console.error("ctxFn.flowDynamic no es una función. Métodos disponibles en ctxFn:", Object.keys(ctxFn));
                }
            } else {
                if (typeof ctxFn.flowDynamic === 'function') {
                    await ctxFn.flowDynamic([{ body: chatbotResponse }]);
                } else {
                    console.error("ctxFn.flowDynamic no es una función. Métodos disponibles en ctxFn:", Object.keys(ctxFn));
                }
            }
        }
    } catch (error) {
        console.error("Error al procesar la nota de voz:", error);
        if (typeof ctxFn.flowDynamic === 'function') {
            await ctxFn.flowDynamic([{ body: "Lo siento, ocurrió un error inesperado al procesar tu nota de voz." }]);
        } else {
            console.error("ctxFn.flowDynamic no es una función. Métodos disponibles en ctxFn:", Object.keys(ctxFn));
        }
    }
});

// Función para convertir dirección a coordenadas usando la API de Google Maps
async function convertAddressToCoordinates(address) {
    const apiKey = 'AIzaSyBRlPWGEbAQ0cZa-myo6PQPpMMWovKBDA4';
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${apiKey}`;

    try {
        const response = await axios.get(url);
        if (response.data.status === 'OK') {
            const location = response.data.results[0].geometry.location;
            console.log(`📍 Dirección: ${address}`);
            console.log(`📍 Coordenadas obtenidas: Latitud ${location.lat}, Longitud ${location.lng}`);
            return {
                latitude: location.lat,
                longitude: location.lng
            };
        } else {
            throw new Error('No se pudo obtener las coordenadas');
        }
    } catch (error) {
        console.error('Error al convertir la dirección a coordenadas:', error);
        throw error;
    }
}

const humanAgent = '573185386235@s.whatsapp.net';

const sendToHumanAgent = async (provider, message) => {
  
    console.log('Mensaje a enviar:', message);

    if (!provider) {
        console.error('Proveedor de Baileys no está definido.');
        return;
    }

    try {
        await provider.sendText(humanAgent, message);
        console.log('Mensaje enviado al agente humano.');
    } catch (error) {
        console.error('Error al enviar mensaje al agente humano:', error);
    }
};

const flowRecopilarDatos = addKeyword(EVENTS.ACTION)
    .addAnswer('Si te interesa contratar el servicio, envíanos los siguientes datos: 📑\n✓ Nombre completo del titular.', {
        capture: true
    }, async (ctx, { flowDynamic, state }) => {
        await state.update({ name: ctx.body });
        await flowDynamic('Gracias por tu nombre');
    })
    .addAnswer('¿Cuál es tu número de cédula del titular?', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ idNumber: ctx.body });
        await flowDynamic('Gracias por tu número de cédula.');
    })
    .addAnswer('¿Cuál es tu dirección completa de residencia?', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ address: ctx.body });
        await flowDynamic('Gracias por tu dirección. ');
    })
    .addAnswer('¿Cuáles son los dos números de celular de contacto?', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ contactNumbers: ctx.body });
        await flowDynamic('Gracias por los números de contacto');
    })
    .addAnswer('Por favor, envía una fotografía del recibo de energía.', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ energyBill: ctx.body });
        await flowDynamic('Gracias por la fotografía');
    })
    .addAnswer('¿Cuál es tu correo electrónico?', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ email: ctx.body });
        await flowDynamic('Gracias por tu correo.');
    })
    .addAnswer('¿Qué plan deseas contratar?', { capture: true }, async (ctx, { flowDynamic, state }) => {
        await state.update({ plan: ctx.body });
        const myState = state.getMyState();
        console.log('Datos recopilados:', myState);
        await flowDynamic(`Tus datos son:\nNombre: ${myState.name}\nNúmero de cédula: ${myState.idNumber}\nDirección: ${myState.address}\nNúmeros de contacto: ${myState.contactNumbers}\nCorreo electrónico: ${myState.email}\nPlan: ${myState.plan}`);

    })
    .addAnswer('¿Son estos datos correctos? (Responde con sí o no)', { capture: true }, async (ctx, { flowDynamic, state, provider, gotoFlow }) => {
        const myState = state.getMyState();
        console.log('Proveedor recibido:', provider);
        if (ctx.body.toLowerCase() === 'sí' || ctx.body.toLowerCase() === 'si') {
            const message = `Tienes un agendamiento de instalación pendiente en el celular de ventas para el siguiente usuario:\n\nNombre: ${myState.name}\nNúmero de cédula: ${myState.idNumber}\nDirección: ${myState.address}\nNúmeros de contacto: ${myState.contactNumbers}\nCorreo electrónico: ${myState.email}\nPlan: ${myState.plan}`;
            
            // Enviar mensaje al agente humano
            await sendToHumanAgent(provider, message);

            await flowDynamic('Perfecto, he recopilado tus datos y te voy a dirigir con el asesor de ventas Martin Capablanca.');
        } else {
            await flowDynamic('Por favor, reinicia el proceso y proporciona los datos correctos.');
            state.clear(); // Limpiar estado para reiniciar el flujo
            return gotoFlow(flowRecopilarDatos); // Redirigir al inicio del flujo de recopilación de datos
        }
    });

const flowVerificarCobertura = addKeyword(EVENTS.ACTION)
    .addAnswer("Por favor, envía tu ubicación ahora para verificar la cobertura.📍", {
        capture: true,
        waitForLocation: true
    }, async (ctx, { flowDynamic, gotoFlow, state, provider }) => {
        console.log('Datos usuario:📍📍 ', ctx);
        if (ctx.message && ctx.message.locationMessage) {
            const latitude = ctx.message.locationMessage.degreesLatitude;
            const longitude = ctx.message.locationMessage.degreesLongitude;
            try {
                console.log(`📍 Ubicación recibida: Latitud ${latitude}, Longitud ${longitude}`);
                const result = await predictCoverageFromCoordinates(latitude, longitude);
                const message = result.hasCoverage ? '¡Tenemos cobertura en tu área!' : '🚀 Actualmente se está expandiendo la cobertura en tu sector, estamos confirmando con el área técnica si ya se cuenta con la disponibilidad inmediata... En breve responderemos a tu mensaje.';
                await flowDynamic(message);

                if (result.hasCoverage) {
                    // Redirigir al siguiente flujo si hay cobertura
                    await state.update({ hasCoverage: true });
                    return gotoFlow(flowRecopilarDatos);
                } else {
                    // Notificar al agente humano si no hay cobertura
                    const userMessage = 'Por favor espera un momento!';
                    const agentMessage = `Usuario con número ${ctx.from} y nombre ${ctx.pushName} ha recibido una predicción de no cobertura. Por favor, verifique manualmente.`;

                    await flowDynamic(userMessage);
                    await sendToHumanAgent(provider, agentMessage);
                }
            } catch (error) {
                await flowDynamic('❌ Hubo un error al verificar la cobertura. Por favor, intenta nuevamente más tarde.');
            }
        } else {
            await flowDynamic('❌ No se recibió una ubicación válida. Por favor, intenta enviar tu ubicación nuevamente.');
            // Mantener el estado hasta recibir una ubicación válida
            state.update({ waitingForValidLocation: true });
            return gotoFlow(flowVerificarCobertura);
        }
    });



    
const flowSectorSanadolfo = addKeyword(EVENTS.ACTION)

    .addAnswer(plan_rural_sanadolfo)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });


const flowSectorQuituro = addKeyword(EVENTS.ACTION)
    .addAnswer(plan_rural_quituro)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });

const flowSectorRuralCaserio = addKeyword(EVENTS.ACTION)
    .addAnswer(plan_rural_caserio)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });

const flowSectorRuralSanroque = addKeyword(EVENTS.ACTION)
    .addAnswer(plan_rural_sanroque)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });

const flowSectorRural = addKeyword(EVENTS.ACTION)
    .addAnswer(plan_rural)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });

const flowSectorUrbano = addKeyword(EVENTS.ACTION)
    .addAnswer(plan_urbano)
    .addAnswer("🗺 Para verificar la cobertura de nuestro servicio en tu área, por favor envíanos tu ubicación. 📍🌍", {
        delay: 2000 // Aquí agregas el delay de 2 segundos
    })
    .addAnswer("Sigue los pasos de este video desde el lugar para donde solicita el servicio!Es muy fácil!", {
        media: "https://bots.fututel.com/video_muestra.mp4"
    }, async (_, { gotoFlow }) => {
        // Redirigir al flujo de verificación de cobertura
        gotoFlow(flowVerificarCobertura);
    });

const flowServicios = addKeyword(EVENTS.ACTION).addAnswer(
    menu_planes,
    {
      capture: true,
    },
    async (ctx, { gotoFlow, fallback, flowDynamic }) => {
        console.log('datos usuario: ',ctx);
      if (!["1", "2", "3", "4","5","6","7","0"].includes(ctx.body)) {
        return fallback("Respuesta no válida, por favor selecciona una de las opciones.");
      }
  
      switch (ctx.body) {
        case "1":
          return  gotoFlow(flowSectorUrbano);
        case "2":
          return  gotoFlow(flowSectorRural);
        case "3":
          return  gotoFlow(flowSectorRuralSanroque);
        case "4":
          return  gotoFlow(flowSectorRuralCaserio);
        case "5":
            return  gotoFlow(flowSectorQuituro);
        case "6":
            return  gotoFlow(flowSectorSanadolfo);
        case "0":
          return  await flowDynamic("Saliendo... Puedes volver a acceder a este menú escribiendo *Menu*");
      }
    }
  );

const flowFacturas = addKeyword(EVENTS.ACTION)
  .addAnswer(
      '👋🏻 ¡Hola! Gracias por contactarnos. Para asuntos relacionados con facturación, por favor comunícate al siguiente contacto:\n\n' +
      '👤 3163123623\n\n' +
      'Nota: Dale click sobre el número y presiona "chatear con" para ir directamente a la conversación con el agente de facturación que te atenderá.'
  );

const flowSoporte = addKeyword(EVENTS.ACTION)
    .addAnswer(
        'Para temas relacionados con inconvenientes con el servicio, por favor comunicarse con el área de 🖥 Soporte Técnico. Para la verificación de tu internet. 🛠\n\n' +
        '👨‍🔧SOPORTE TECNICO 1 📲 3188724601\n' +
        '👩🏻‍🔧SOPORTE TECNICO 2 📲 3163290810\n' +
        '👨🏽‍🔧SOPORTE TECNICO 3 📲 3157155285\n\n' +
        'Nota: Dale click sobre el número y presiona "Chatear con" para ir directamente a la conversación con el agente de soporte que te atenderá.'
    );

const flowOtrasConsultas = addKeyword(EVENTS.ACTION)
    .addAnswer('Por favor, proporciona más detalles sobre tu consulta.')
    .addAction({ capture: true }, async (ctx, { flowDynamic }) => {
        const userMessage = ctx.body;
        console.log("mensaje a enviar al chatbot: ",userMessage);
        const reply = await queryExternalChatbot(userMessage);
        await flowDynamic(reply);
    });

const flowPrincipal = addKeyword([
        'hola', 
        'ole', 
        'alo', 
        'buenos dias', 
        'buenas tardes', 
        'buenas noches', 
        'menu', 
        'quiero internet', 
        'solicitar internet', 
        'contratar internet', 
        'servicio de internet', 
        'planes de internet', 
        'internet hogar', 
        'internet para mi casa', 
        'cobertura de internet', 
        'instalación de internet', 
        'internet barato', 
        'mejor internet', 
        'precio de internet', 
        'cotización internet', 
        'internet empresarial', 
        'internet oficina', 
        'wifi', 
        'internet fibra óptica', 
        'internet alta velocidad', 
        'paquetes de internet', 
        'velocidad de internet', 
        'internet ilimitado', 
        'internet prepago', 
        'internet mensual', 
        'promociones de internet'
        ])
        .addAnswer(
        menu,
        {
          capture: true,
        },
        async (ctx, { gotoFlow, fallback, flowDynamic }) => {
            console.log('datos usuario: ',ctx);
          if (!["1", "2", "3", "4","0"].includes(ctx.body)) {
            return fallback("Respuesta no válida, por favor selecciona una de las opciones.");
          }
      
          switch (ctx.body) {
            case "1":
              return  gotoFlow(flowServicios);
            case "2":
              return  gotoFlow(flowFacturas);
            case "3":
              return  gotoFlow(flowSoporte);
            case "4":
              return  gotoFlow(flowOtrasConsultas);
            case "0":
              return  await flowDynamic("Saliendo... Puedes volver a acceder a este menú escribiendo *Menu*");
          }
        }
      );

const main = async () => {
    const adapterDB = new MySQLAdapter({
        host: MYSQL_DB_HOST,
        user: MYSQL_DB_USER,
        database: MYSQL_DB_NAME,
        password: MYSQL_DB_PASSWORD,
        port: MYSQL_DB_PORT,
    })
    const adapterFlow = createFlow([flowPrincipal,flowServicios,flowFacturas,flowSoporte,flowOtrasConsultas,flowSectorUrbano,flowSectorRural,flowSectorRuralSanroque,flowSectorRuralCaserio,flowSectorQuituro,flowSectorSanadolfo ,flowVerificarCobertura,flowRecopilarDatos,flowVoice])
    const adapterProvider = createProvider(BaileysProvider)
    createBot({
        flow: adapterFlow,
        provider: adapterProvider,
        database: adapterDB,
    })
    QRPortalWeb()
}


main()
