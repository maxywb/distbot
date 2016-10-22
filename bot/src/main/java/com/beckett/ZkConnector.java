package com.beckett;

import com.google.common.util.concurrent.ThreadFactoryBuilder;
import org.apache.curator.framework.CuratorFramework;
import org.apache.curator.framework.CuratorFrameworkFactory;
import org.apache.curator.framework.recipes.cache.TreeCache;
import org.apache.curator.framework.recipes.cache.TreeCacheEvent;
import org.apache.curator.framework.recipes.cache.TreeCacheListener;
import org.apache.curator.retry.ExponentialBackoffRetry;
import org.apache.zookeeper.CreateMode;

import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.ThreadFactory;

/**
 * Created by meatwad on 10/22/16.
 */
public class ZkConnector {
    private CuratorFramework client;
    private List<TreeCache> caches = new LinkedList();

    ZkConnector(String connectionString) {

        ThreadFactory threadFactory = new ThreadFactoryBuilder().setNameFormat("CuratorInstance Curator - %d").setDaemon(true).build();
        CuratorFrameworkFactory.Builder curatorBuilder = CuratorFrameworkFactory
                .builder()
                .connectString(connectionString)
                .retryPolicy(new ExponentialBackoffRetry(1000, 10))
                .threadFactory(threadFactory);

        client = curatorBuilder.build();
        client.start();
    }

    public void blockUntilConnected() throws InterruptedException {
        client.blockUntilConnected();

    }

    public void create(String path) throws Exception {

        create(path, "");
    }

    public void create(String path, String payload) throws Exception {
        client.create().creatingParentContainersIfNeeded().forPath(path, payload.getBytes());
    }

    public void create(String path, byte[] payload) throws Exception {
        client.create().creatingParentContainersIfNeeded().forPath(path, payload);
    }

    public void createEphemeral(String path) throws Exception {

        createEphemeral(path, "");
    }

    public void createEphemeral(String path, String payload) throws Exception {
        client.create().creatingParentContainersIfNeeded().withMode(CreateMode.EPHEMERAL).forPath(path, payload.getBytes());
    }

    public void createEphemeral(String path, byte[] payload) throws Exception {
        client.create().creatingParentContainersIfNeeded().withMode(CreateMode.EPHEMERAL).forPath(path, payload);
    }

    public void update(String path, String payload) throws Exception {
        client.setData().forPath(path, payload.getBytes());
    }

    public void update(String path, byte[] payload) throws Exception {
        client.setData().forPath(path, payload);
    }

    public void delete(String path) throws Exception {
        client.delete().deletingChildrenIfNeeded().forPath(path);
    }

    public <T> T getData(String path, Class<T> clazz) throws Exception {
        return clazz.getConstructor(byte[].class).newInstance(client.getData().forPath(path));
    }

    public List<String> getChildren(String path) throws Exception {

        return client.getChildren().forPath(path);
    }

    public void registerTreeListener(String path, TreeCacheListener listener) throws Exception {

        TreeCache cache = new TreeCache(client, path);
        cache.getListenable().addListener(listener);
        cache.start();
        caches.add(cache);
    }

    public static void main(String[] args) throws Exception {


        ZkConnector client = new ZkConnector("192.168.1.201:2181");
        client.blockUntilConnected();
        client.delete("/test");

        List<String> paths = Arrays.asList(
                "/test/foo/goo",
                "/test/foo/bar",
                "/test/foo/baz"
        );

        System.out.println("create");
        for (String p : paths) {
            String data = "data-" + p;
            client.create(p, data);
        }
        for (String child : client.getChildren("/test/foo")) {
            System.out.println(child);
        }

        System.out.println("get");
        for (String p : paths) {
            String data = client.getData(p, String.class);
            System.out.println(String.format("%s : %s", p, data));
        }

        System.out.println("update");
        for (String p : paths) {
            String data = "updated! - " + p;
            client.update(p, data);
        }
        for (String p : paths) {
            String data = client.getData(p, String.class);
            System.out.println(String.format("%s : %s", p, data));
        }

        System.out.println("delete");
        client.delete("/test/foo");
        for (String child : client.getChildren("/test")) {
            System.out.println(child);
        }

    }
}
