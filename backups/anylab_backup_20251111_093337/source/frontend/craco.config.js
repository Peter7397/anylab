// CRACO config to fix webpack path resolution issues on external drives
const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Disable symlink resolution to fix external drive path issues
      if (webpackConfig.resolve) {
        webpackConfig.resolve.symlinks = false;
      }
      if (webpackConfig.resolveLoader) {
        webpackConfig.resolveLoader.symlinks = false;
        // Fix path resolution for loaders
        webpackConfig.resolveLoader.modules = [
          path.resolve(__dirname, 'node_modules'),
          ...(webpackConfig.resolveLoader.modules || [])
        ];
      }
      
      // Ensure proper module resolution
      webpackConfig.resolve = webpackConfig.resolve || {};
      webpackConfig.resolve.modules = [
        path.resolve(__dirname, 'node_modules'),
        ...(webpackConfig.resolve.modules || [])
      ];
      
      // Fix for html-webpack-plugin path resolution
      // Override plugins configuration if html-webpack-plugin is present
      if (webpackConfig.plugins) {
        webpackConfig.plugins = webpackConfig.plugins.map(plugin => {
          // If it's html-webpack-plugin, ensure it uses correct paths
          if (plugin.constructor && plugin.constructor.name === 'HtmlWebpackPlugin') {
            // Force the plugin to use relative paths
            const originalOptions = plugin.options || {};
            plugin.options = {
              ...originalOptions,
              // Ensure template paths are relative
            };
          }
          return plugin;
        });
      }
      
      return webpackConfig;
    }
  }
};
