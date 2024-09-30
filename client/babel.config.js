const path = require('path');

module.exports = {
  presets: [
    '@vue/cli-plugin-babel/preset'
  ],
  overrides: [{
    test: /\.js$/,
    include: [
      path.resolve(__dirname, '../common')
    ]
  }]
}