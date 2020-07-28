import React, { useState } from 'react';
import { Grid } from '@material-ui/core';
import * as constants from './common/constants';
import Snackbar from '@material-ui/core/Snackbar';
import Alert from '@material-ui/lab/Alert';
import axios from 'axios';
import ProcessorCard from './common/components/ProcessorCard';

const initState = () => {
  /*In future releases, it should be a fetched array from the API*/
  return {
    processors: [
      {
        host: localStorage.getItem(constants.processorHostStorageKey)
          || '0.0.0.0',
        port: localStorage.getItem(constants.processorPortStorageKey)
          || '8300',
        videoPath: localStorage.getItem(constants.processorVideoPathStorageKey)
          || 'Not defined'
      }
    ]
  };
};

export default function Settings() {
  const [state, setState] = useState(initState());

  const saveConfig = async (processor, index) => {
    if (!processor) {
      setState({
        ...state,
        showMsg: true,
        severity: 'error',
        alertMsg: 'All fields are required'
      });
      return;
    }

    try {
      const url = `http://${processor.host}:${processor.port}/config`;
      const response = await axios.put(url, {
        app: {
          video_path: processor.videoPath
        }
      });
      localStorage.setItem(constants.processorPortStorageKey, processor.port);
      localStorage.setItem(constants.processorHostStorageKey, processor.host);
      localStorage.setItem(constants.processorVideoPathStorageKey,
        processor.videoPath)

      const updatedProcessors = [...state.processors];
      updatedProcessors[index] = processor;

      setState({
        ...state,
        processors: updatedProcessors,
        showMsg: true,
        severity: 'success',
        alertMsg: 'Configuration saved successfully.'
      });
    } catch (e) {
      const response = e.response.data;

      const errors = response.detail.map(error => (
        <p>{error.msg}</p>
      ));

      errors.unshift(<p>An error occurred while trying to save the
        configuration.</p>);

      setState({
        ...state,
        showMsg: true,
        severity: 'error',
        alertMsg: errors
      })
    }
  };

  const handleClose = () => {
    setState({
      ...state,
      showMsg: false
    });
  }

  return (
    <Grid container spacing={3} direction="column">
      <h1>Settings</h1>

      {state.showMsg &&
      <Snackbar open={state.showMsg}
                style={{ marginTop: '45px' }}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
                autoHideDuration={4000}
                onClose={handleClose}>
        <Alert onClose={handleClose} severity={state.severity}>
          {state.alertMsg}
        </Alert>
      </Snackbar>
      }

      <h3>Processor configuration</h3>

      <Grid container spacing={2} direction="row" wrap>

        {state.processors.map((processor, index) => (
          <ProcessorCard
            processor={processor}
            saveFn={saveConfig}
            index={index}
          />
        ))}
      </Grid>
    </Grid>
  );
}
