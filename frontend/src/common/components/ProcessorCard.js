import { makeStyles } from '@material-ui/core/styles';
import React, { useState } from 'react';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import { Grid, Link } from '@material-ui/core';
import TextField from '@material-ui/core/TextField';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Checkbox from '@material-ui/core/Checkbox';

const useStyle = makeStyles((theme) => ({
  cardContainer: {
    width: '300px',
    height: '200px',
  },
  linkContainer: {
    textAlign: 'end'
  },
  cardLink: {
    marginLeft: '5px'
  },
  cardLabel: {
    color: 'rgba(0, 0, 0, 0.54)',
    marginTop: '10px'
  }
}));

export default function ProcessorCard({ processor, saveFn, index }) {
  const classes = useStyle();
  const [state, setState] = useState({
    host: processor.host || '',
    port: processor.port || '',
    videoPath: processor.videoPath || '',
    saveOnDisk: false,
    edit: false
  });

  const handleOnChangeFields = (e) => {
    const newState = { ...state };

    newState[e.target.name] = e.target.name === 'saveOnDisk' ? e.target.checked
      : e.target.value;
    setState(newState);
  };

  const toggleEdit = () => {
    setState({
      ...state,
      edit: !state.edit
    });
  };

  const handleSave = () => {
    if (!state.port || !state.host || !state.videoPath) {
      saveFn(undefined, index);
    } else {
      saveFn({
        host: state.host,
        port: state.port,
        videoPath: state.videoPath,
        saveOnDisk: state.saveOnDisk
      }, index);
      setState({
        ...state,
        edit: false
      });
    }
  };

  return (
    <Card>
      <CardContent>
        <Grid className={classes.cardContainer} container
              direction="row">
          <Grid item xs={12} md={8}>
            Processor {index + 1}
          </Grid>
          <Grid className={classes.linkContainer} item xs={12} md={4}>
            {!state.edit ?
              <Link component="button" onClick={toggleEdit}>Edit</Link>
              :
              <>
                <Link component="button" onClick={toggleEdit}>Cancel</Link>
                <Link component="button" className={classes.cardLink}
                      onClick={handleSave}>Save</Link>
              </>
            }
          </Grid>
          <Grid item xs={12} md={12}>
            {state.edit ?
              <TextField
                fullWidth
                label="Host"
                name="host"
                value={state.host}
                onChange={handleOnChangeFields}
              />
              :
              <div>
                <div className={classes.cardLabel}>Host</div>
                <div>{processor.host}</div>
              </div>
            }
          </Grid>
          <Grid item xs={12} md={12}>
            {state.edit ? <TextField
                fullWidth
                label="Port"
                name="port"
                value={state.port}
                onChange={handleOnChangeFields}
              />
              :
              <div>
                <div className={classes.cardLabel}>Port</div>
                <div>{processor.port}</div>
              </div>
            }
          </Grid>
          {state.edit ?
            <TextField
              fullWidth
              label="Video Path"
              name="videoPath"
              value={state.videoPath}
              onChange={handleOnChangeFields}
            />
            :
            <div>
              <div className={classes.cardLabel}>Video Path</div>
              <div>{processor.videoPath}</div>
            </div>
          }
        </Grid>
        {state.edit &&
        <Grid item xs={12} md={12}>
          <FormControlLabel
            control={
              <Checkbox
                checked={state.saveOnDisk}
                onChange={handleOnChangeFields}
                name="saveOnDisk"
                color="primary"
              />
            }
            label="Save configuration on disk?"
          />
        </Grid>
        }
      </CardContent>

    </Card>
  );
}
