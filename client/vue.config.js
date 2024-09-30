const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),  // Alias for src folder
        '@common': path.resolve(__dirname, '../../common')  // Adjusted path for the common folder
      }
    }
  }
});