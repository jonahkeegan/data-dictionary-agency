const path = require('path');

module.exports = {
  entry: './src/visualization/index.js',
  output: {
    filename: 'visualization.bundle.js',
    path: path.resolve(__dirname, 'dist'),
    library: 'DataDictionaryVisualization',
    libraryTarget: 'umd',
    globalObject: 'this'
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  },
  resolve: {
    extensions: ['.js']
  },
  devtool: 'source-map',
  mode: 'development'
};
