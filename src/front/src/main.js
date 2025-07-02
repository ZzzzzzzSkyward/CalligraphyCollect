import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/css/app.css'
import '@/css/fluentdesign.css'
import '@/css/global.css'
import vue3PreviewImage from 'vue3-preview-image'
import VxeTable from 'vxe-table'
import VxeUI from 'vxe-pc-ui'
import 'vxe-table/lib/style.css'
import 'vxe-pc-ui/lib/style.css'
const app = createApp( App )
app.use( ElementPlus )
app.use( vue3PreviewImage, { showDownloadBtn: true } )
app.use(VxeTable)
app.use(VxeUI)
app.mount( '#app' )
