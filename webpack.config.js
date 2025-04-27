const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: {
    visualization: './src/visualization/index.js',
    app: './src/ui/index.js'
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, 'dist'),
    library: {
      name: 'DataDictionaryAgency',
      type: 'umd',
      export: 'default',
    },
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
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/ui/index.html',
      filename: 'index.html',
      excludeChunks: ['visualization']
    })
  ],
  devtool: 'source-map',
  mode: 'development',
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 3000,
    hot: true,
    historyApiFallback: true
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
    },
  },
};
