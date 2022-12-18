import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import colors from 'vuetify/lib/util/colors'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { md3 } from 'vuetify/blueprints'

// import './assets/main.css'

const customDarkTheme = {
    dark: true,
    colors: {
        background: '#151018',
        surface: '#2B2131',
        primary: '#E4A33A',
        secondary: '#EF2D56',
        info: '#9BC995',
        anchor: '#EF2D56'
    }
  }
  

const vuetify = createVuetify({
    blueprint: md3,
    icons: {
        defaultSet: 'mdi',
        aliases,
        sets: {
          mdi,
        }
    },
    theme: {
        defaultTheme: 'customDarkTheme',
        themes: {
            customDarkTheme
        }
    },
    components,
    directives,
})

const app = createApp(App)

app.provide('baseUrlApi', "https://flickflock-backend-vr3q5dt6va-ew.a.run.app/api")

app.use(vuetify)
app.use(router)

app.mount('#app')
